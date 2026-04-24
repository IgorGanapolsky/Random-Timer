package com.iganapolsky.randomtimer.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.media.MediaPlayer
import android.media.Ringtone
import android.media.RingtoneManager
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log
import androidx.core.app.NotificationCompat
import com.iganapolsky.randomtimer.MainActivity
import com.iganapolsky.randomtimer.R
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsProperties
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.model.pickRandomDurationMillisInclusive
import com.iganapolsky.randomtimer.notifications.ReengagementScheduler
import com.iganapolsky.randomtimer.receiver.ScreenOffReceiver
import com.iganapolsky.randomtimer.review.StoreReviewManager
import com.iganapolsky.randomtimer.stats.TrainingStatsService
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import javax.inject.Inject
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

@AndroidEntryPoint
class TimerForegroundService : Service() {
    @Inject lateinit var storeReviewManager: StoreReviewManager

    @Inject lateinit var analyticsService: AnalyticsService

    @Inject lateinit var proManager: ProManager

    @Inject lateinit var voiceCalloutManager: AIVoiceCalloutManager

    @Inject lateinit var packStore: ProAudioPackStore

    private val trainingStatsService by lazy { TrainingStatsService(this) }
    private val binder = LocalBinder()
    private val serviceScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var timerJob: Job? = null

    private val _timerState = MutableStateFlow<TimerState?>(null)
    val timerState: StateFlow<TimerState?> = _timerState.asStateFlow()

    private lateinit var notificationManager: NotificationManager
    private var isAppInForeground = false
    private var isForegroundNotificationActive = false

    private var audioFocusRequest: AudioFocusRequest? = null
    private var vibrator: Vibrator? = null
    private var screenOffReceiver: ScreenOffReceiver? = null
    private var wakeLock: PowerManager.WakeLock? = null

    inner class LocalBinder : Binder() {
        fun getService(): TimerForegroundService = this@TimerForegroundService
    }

    override fun onCreate() {
        super.onCreate()
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        vibrator =
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val manager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                manager.defaultVibrator
            } else {
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            }
        createNotificationChannels()
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onStartCommand(
        intent: Intent?,
        flags: Int,
        startId: Int,
    ): Int {
        if (intent?.hasExtra(EXTRA_APP_IN_FOREGROUND) == true) {
            isAppInForeground = intent.getBooleanExtra(EXTRA_APP_IN_FOREGROUND, isAppInForeground)
        }
        when (intent?.action) {
            ACTION_APP_STATE_CHANGED -> {
                isAppInForeground = intent.getBooleanExtra(EXTRA_APP_IN_FOREGROUND, false)
                _timerState.value?.let { updateNotification(it) } ?: removeForegroundNotification()
            }
            ACTION_UPDATE_LOOP -> {
                val repeatEnabled = intent.getBooleanExtra(EXTRA_REPEAT_ENABLED, false)
                updateLoopSetting(repeatEnabled)
            }
            ACTION_UPDATE_VOICE -> {
                val voiceEnabled = intent.getBooleanExtra(EXTRA_VOICE_ENABLED, false)
                updateVoiceSetting(voiceEnabled)
            }
            ACTION_START -> {
                val targetMs = intent.getLongExtra(EXTRA_TARGET_DURATION_MS, 0L)
                val remainingMs = intent.getLongExtra(EXTRA_REMAINING_DURATION_MS, targetMs)
                val minSeconds = intent.getIntExtra(EXTRA_MIN_SECONDS, 30)
                val maxSeconds = intent.getIntExtra(EXTRA_MAX_SECONDS, 120)
                val alarmDuration = intent.getIntExtra(EXTRA_ALARM_DURATION, 10)
                val hiddenMode = intent.getBooleanExtra(EXTRA_HIDDEN_MODE, false)
                val repeatEnabled = intent.getBooleanExtra(EXTRA_REPEAT_ENABLED, false)
                val soundType = intent.getStringExtra(EXTRA_SOUND_TYPE) ?: "INTENSE"
                val volume = intent.getFloatExtra(EXTRA_VOLUME, 1.0f)
                val vibrationEnabled = intent.getBooleanExtra(EXTRA_VIBRATION_ENABLED, true)
                val useExtendedRange = intent.getBooleanExtra(EXTRA_USE_EXTENDED_RANGE, false)
                val voiceEnabled = intent.getBooleanExtra(EXTRA_VOICE_ENABLED, false)
                val repeatRounds = intent.getIntExtra(EXTRA_REPEAT_ROUNDS, 0)
                val roundCount = intent.getIntExtra(EXTRA_ROUND_COUNT, 1)

                if (targetMs > 0) {
                    startTimerFromExtras(
                        targetMs = targetMs,
                        remainingMs = remainingMs,
                        minSeconds = minSeconds,
                        maxSeconds = maxSeconds,
                        alarmDuration = alarmDuration,
                        hiddenMode = hiddenMode,
                        repeatEnabled = repeatEnabled,
                        soundType = soundType,
                        volume = volume,
                        vibrationEnabled = vibrationEnabled,
                        useExtendedRange = useExtendedRange,
                        voiceEnabled = voiceEnabled,
                        repeatRounds = repeatRounds,
                        roundCount = roundCount,
                    )
                }
            }
            ACTION_STOP -> {
                val stopSource =
                    if (intent.getBooleanExtra(EXTRA_APP_IN_FOREGROUND, false)) {
                        STOP_SOURCE_APP
                    } else {
                        STOP_SOURCE_NOTIFICATION
                    }
                stopTimer(
                    stopSource = stopSource,
                    trackStopAnalytics = true,
                )
            }
            ACTION_PAUSE -> pauseTimer()
            ACTION_RESUME -> resumeTimer()
            ACTION_RESET -> resetTimer()
            ACTION_DISMISS_ALARM -> dismissAlarm()
            ACTION_SILENCE_ALARM -> silenceAlarm()
        }
        return START_STICKY
    }

    private fun updateLoopSetting(repeatEnabled: Boolean) {
        _timerState.value?.let { current ->
            val updatedConfig =
                current.config.copy(
                    repeatEnabled = repeatEnabled,
                    useExtendedRange = current.config.useExtendedRange,
                    voiceEnabled = current.config.voiceEnabled,
                    repeatRounds = current.config.repeatRounds,
                )
            _timerState.value = current.copy(config = updatedConfig)
        }
    }

    private fun updateVoiceSetting(voiceEnabled: Boolean) {
        _timerState.value?.let { current ->
            val updatedConfig =
                current.config.copy(
                    voiceEnabled = voiceEnabled,
                    repeatEnabled = current.config.repeatEnabled,
                    useExtendedRange = current.config.useExtendedRange,
                    repeatRounds = current.config.repeatRounds,
                )
            _timerState.value = current.copy(config = updatedConfig)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        removeForegroundNotification()
        abandonAudioFocus()
        stopAlarmSound()
        stopVibration()
        unregisterScreenOffReceiver()
        releaseTimerWakeLock()
        voiceCalloutManager.shutdown()
        serviceScope.cancel()
    }

    override fun onTaskRemoved(rootIntent: Intent?) {
        super.onTaskRemoved(rootIntent)
        // Keep the foreground service running when user swipes app from recents.
        // The timer should continue counting down and trigger the alarm normally.
        // Ensure we have a visible notification so the OS doesn't kill us.
        _timerState.value?.let { state ->
            updateNotification(state)
        }
    }

    private fun startTimerFromExtras(
        targetMs: Long,
        remainingMs: Long,
        minSeconds: Int,
        maxSeconds: Int,
        alarmDuration: Int,
        hiddenMode: Boolean,
        repeatEnabled: Boolean,
        soundType: String,
        volume: Float,
        vibrationEnabled: Boolean,
        useExtendedRange: Boolean = false,
        voiceEnabled: Boolean = false,
        repeatRounds: Int = 0,
        roundCount: Int = 1,
    ) {
        val config =
            TimerConfig(
                minSeconds = minSeconds,
                maxSeconds = maxSeconds,
                alarmDuration = alarmDuration,
                hiddenMode = hiddenMode,
                repeatEnabled = repeatEnabled,
                soundType =
                    try {
                        SoundType.valueOf(soundType)
                    } catch (_: Exception) {
                        SoundType.INTENSE
                    },
                volume = volume,
                vibrationEnabled = vibrationEnabled,
                useExtendedRange = useExtendedRange,
                voiceEnabled = voiceEnabled,
                repeatRounds = repeatRounds,
            )

        val initialState =
            TimerState(
                config = config,
                targetDuration = targetMs.milliseconds,
                remainingDuration = remainingMs.milliseconds,
                status = TimerStatus.RUNNING,
                roundCount = roundCount,
            )

        startTimer(initialState)
    }

    private fun startTimer(initialState: TimerState) {
        acquireTimerWakeLock()
        _timerState.value = initialState
        updateNotification(initialState)
        voiceCalloutManager.resetSession()
        if (proManager.entitlementLevel.value.isPro && initialState.config.voiceEnabled) {
            voiceCalloutManager.beginSession(
                totalDurationSeconds = initialState.targetDuration.inWholeSeconds.toInt(),
                gender = initialState.config.voiceGender,
            )
        }

        timerJob?.cancel()
        timerJob =
            serviceScope.launch {
                var state = initialState

                while (isActive && state.status != TimerStatus.COMPLETE) {
                    delay(1000)

                    val newRemaining =
                        (state.remainingDuration - 1.seconds)
                            .coerceAtLeast(kotlin.time.Duration.ZERO)

                    // Random timer - don't reveal warning/danger, just running until complete
                    val newStatus =
                        when {
                            newRemaining <= kotlin.time.Duration.ZERO -> TimerStatus.COMPLETE
                            else -> TimerStatus.RUNNING
                        }

                    // Update from current _timerState to preserve config changes
                    // (e.g. loop toggle) made between ticks
                    val current = _timerState.value ?: state
                    state =
                        current.copy(
                            remainingDuration = newRemaining,
                            status = newStatus,
                        )

                    _timerState.value = state
                    updateNotification(state)

                    // Trigger AI voice callouts for Pro users using elapsed time, not remaining time.
                    if (proManager.entitlementLevel.value.isPro && state.config.voiceEnabled) {
                        val elapsedSeconds = (state.targetDuration - newRemaining).inWholeSeconds.toInt()
                        voiceCalloutManager.triggerCallout(elapsedSeconds)
                    }

                    if (newStatus == TimerStatus.COMPLETE) {
                        triggerAlarm(state)
                    }
                }
            }
    }

    private fun stopTimer(
        stopSource: String = STOP_SOURCE_APP,
        trackStopAnalytics: Boolean = false,
    ) {
        val stateBeforeStop = _timerState.value
        if (trackStopAnalytics) {
            trackStopAnalytics(stopSource, stateBeforeStop)
        }
        timerJob?.cancel()
        alarmCountdownJob?.cancel()
        voiceCalloutManager.resetSession()
        abandonAudioFocus()
        stopAlarmSound()
        stopVibration()
        unregisterScreenOffReceiver()
        releaseTimerWakeLock()
        _timerState.value = null
        removeForegroundNotification()
        stopSelf()
    }

    private fun trackStopAnalytics(
        stopSource: String,
        state: TimerState?,
    ) {
        analyticsService.track(
            AnalyticsEvents.TIMER_STOPPED,
            mapOf(AnalyticsProperties.SOURCE to stopSource),
        )
        if (state != null && state.status != TimerStatus.ALARM && state.status != TimerStatus.COMPLETE) {
            val abandonReason =
                if (!isAppInForeground) "app_backgrounded" else "user_cancelled"
            analyticsService.track(
                AnalyticsEvents.TIMER_ABANDONED,
                mapOf(
                    "target_duration" to state.targetDuration.inWholeSeconds,
                    "remaining_duration" to state.remainingDuration.inWholeSeconds,
                    "status" to state.status.name,
                    AnalyticsProperties.SOURCE to stopSource,
                    AnalyticsProperties.ABANDON_REASON to abandonReason,
                ),
            )
        }
    }

    private fun pauseTimer() {
        timerJob?.cancel()
        releaseTimerWakeLock()
        _timerState.value?.let { state ->
            if (state.status != TimerStatus.PAUSED) {
                val pausedState = state.copy(status = TimerStatus.PAUSED)
                _timerState.value = pausedState
                updateNotification(pausedState)
            }
        }
    }

    private fun resumeTimer() {
        _timerState.value?.let { state ->
            if (state.status == TimerStatus.PAUSED) {
                val resumedState = state.copy(status = TimerStatus.RUNNING)
                _timerState.value = resumedState
                startTimer(resumedState)
            }
        }
    }

    private fun resetTimer() {
        timerJob?.cancel()
        alarmCountdownJob?.cancel()
        alarmCountdownJob = null
        removeForegroundNotification()
        abandonAudioFocus()
        stopAlarmSound()
        stopVibration()
        _timerState.value?.let { state ->
            val resetState =
                state.copy(
                    remainingDuration = state.targetDuration,
                    status = TimerStatus.RUNNING,
                    alarmTimeRemaining = kotlin.time.Duration.ZERO,
                    startedAt = System.currentTimeMillis(),
                )
            startTimer(resetState)
        }
    }

    private fun dismissAlarm() {
        alarmCountdownJob?.cancel()
        // Track completion before cleanup — user heard the alarm and acknowledged it
        _timerState.value?.let { state ->
            if (AlarmCompletionPolicy.shouldRecordManualDismissCompletion(state.status)) {
                analyticsService.track(
                    AnalyticsEvents.TIMER_COMPLETED,
                    mapOf(
                        "target_duration" to state.targetDuration.inWholeSeconds,
                        "source" to "alarm_dismissed",
                    ),
                )
                analyticsService.trackFirstTimerCompletedIfNeeded()
                storeReviewManager.recordCompletion()
                trainingStatsService.recordSession()
            }
        }
        abandonAudioFocus()
        stopAlarmSound()
        stopVibration()
        unregisterScreenOffReceiver()
        stopTimer(trackStopAnalytics = false)
    }

    private fun silenceAlarm() {
        // Stop sound/vibration but keep alarm countdown alive for loop support.
        // The countdown continues ticking so that when it reaches 0,
        // the loop logic in startAlarmCountdown() can restart the timer.
        abandonAudioFocus()
        stopAlarmSound()
        stopVibration()
        unregisterScreenOffReceiver()
        releaseTimerWakeLock()

        _timerState.value?.let { current ->
            if (current.status == TimerStatus.ALARM) {
                val silenced = current.copy(isAlarmSilenced = true)
                _timerState.value = silenced
                // Downgrade from alarm notification (fullScreenIntent, HIGH channel)
                // to regular timer notification so the screen stays off after
                // power-button press.
                updateNotification(silenced)
            }
        }
    }

    private fun triggerAlarm(state: TimerState) {
        acquireTimerWakeLock()
        // Update status to ALARM
        _timerState.value =
            state.copy(
                status = TimerStatus.ALARM,
                alarmTimeRemaining = state.config.alarmDuration.seconds,
            )

        registerScreenOffReceiver()
        _timerState.value?.let { updateNotification(it) }

        // Play sound (always enabled, controlled by volume)
        if (state.config.volume > 0f) {
            playAlarmSound()
        }

        // Vibrate if enabled
        if (state.config.vibrationEnabled) {
            startVibration()
        }

        // Start alarm countdown to auto-stop after alarmDuration
        startAlarmCountdown(state.config.alarmDuration)
    }

    private var alarmCountdownJob: Job? = null

    private fun startAlarmCountdown(durationSeconds: Int) {
        alarmCountdownJob?.cancel()
        alarmCountdownJob =
            serviceScope.launch {
                var remaining = durationSeconds
                while (isActive && remaining > 0) {
                    delay(1000)
                    remaining--

                    // Update alarm time remaining in state
                    _timerState.value?.let { current ->
                        _timerState.value =
                            current.copy(
                                alarmTimeRemaining = remaining.seconds,
                            )
                    }
                }

                // Alarm duration finished - stop alarm and check for loop
                if (isActive) {
                    abandonAudioFocus()
                    stopAlarmSound()
                    stopVibration()
                    unregisterScreenOffReceiver()
                    storeReviewManager.recordCompletion()
                    trainingStatsService.recordSession()

                    // Schedule re-engagement reminders so user gets nudged back
                    ReengagementScheduler.schedule(this@TimerForegroundService)

                    val currentState = _timerState.value
                    if (currentState?.config?.repeatEnabled == true) {
                        val shouldContinue =
                            currentState.config.repeatRounds == 0 || currentState.roundCount < currentState.config.repeatRounds
                        if (shouldContinue) {
                            // Auto-restart timer
                            restartTimerInternal()
                        } else {
                            releaseTimerWakeLock()
                            // Loop limit reached - keep state as COMPLETE
                            _timerState.value =
                                currentState.copy(
                                    status = TimerStatus.COMPLETE,
                                    alarmTimeRemaining = 0.seconds,
                                    isAlarmSilenced = false,
                                )
                            _timerState.value?.let { updateNotification(it) }
                        }
                    } else {
                        releaseTimerWakeLock()
                        // Alarm sound finished — keep state as COMPLETE (iOS parity)
                        // User must manually Stop or Reset from the ActiveTimerScreen
                        _timerState.value =
                            currentState?.copy(
                                status = TimerStatus.COMPLETE,
                                alarmTimeRemaining = 0.seconds,
                                isAlarmSilenced = false,
                            )
                        _timerState.value?.let { updateNotification(it) }
                    }
                }
            }
    }

    private fun restartTimerInternal() {
        val currentState = _timerState.value ?: return
        val currentConfig = currentState.config
        val currentRound = currentState.roundCount

        // Track loop round completion before restarting
        analyticsService.track(
            AnalyticsEvents.LOOP_ROUND_COMPLETED,
            mapOf(
                "round_number" to currentRound,
                "round_duration_seconds" to currentState.targetDuration.inWholeSeconds,
            ),
        )

        // Generate new random duration
        val minMs = currentConfig.minSeconds * 1000L
        val maxMs = currentConfig.maxSeconds * 1000L
        val randomMs = pickRandomDurationMillisInclusive(minMs, maxMs, kotlin.random.Random.Default)

        val newState =
            TimerState(
                config = currentConfig,
                targetDuration = randomMs.milliseconds,
                remainingDuration = randomMs.milliseconds,
                status = TimerStatus.RUNNING,
                roundCount = currentRound + 1,
            )

        startTimer(newState)
    }

    private fun acquireTimerWakeLock() {
        val existing = wakeLock
        if (existing?.isHeld == true) {
            return
        }

        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock =
            existing
                ?: powerManager.newWakeLock(
                    PowerManager.PARTIAL_WAKE_LOCK,
                    "$packageName:active_timer",
                ).apply {
                    setReferenceCounted(false)
                }

        runCatching {
            wakeLock?.acquire()
        }.onFailure { error ->
            Log.w("TimerForegroundService", "Failed to acquire timer wake lock", error)
        }
    }

    private fun releaseTimerWakeLock() {
        val current = wakeLock ?: return
        if (!current.isHeld) {
            return
        }
        runCatching {
            current.release()
        }.onFailure { error ->
            Log.w("TimerForegroundService", "Failed to release timer wake lock", error)
        }
    }

    private fun createNotificationChannels() {
        // Timer progress channel — DEFAULT importance so no heads-up in foreground
        val timerChannel =
            NotificationChannel(
                CHANNEL_TIMER,
                "Active Timer",
                NotificationManager.IMPORTANCE_DEFAULT,
            ).apply {
                description = "Shows timer controls in notification shade"
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
                setShowBadge(false)
                setSound(null, null)
                enableVibration(false)
            }

        // Alarm channel (high priority, bypasses DND)
        val alarmChannel =
            NotificationChannel(
                CHANNEL_ALARM,
                "Timer Alarm",
                NotificationManager.IMPORTANCE_HIGH,
            ).apply {
                description = "Alerts when timer completes"
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
                setBypassDnd(true)
                enableVibration(false)
                setShowBadge(true)
                setSound(null, null)
            }

        notificationManager.createNotificationChannels(listOf(timerChannel, alarmChannel))

        // Clean up old media channel if it exists from a previous version
        notificationManager.deleteNotificationChannel(CHANNEL_MEDIA)
    }

    /**
     * Creates Material Design 3 styled timer notification with chronometer countdown.
     *
     * Features:
     * - No countdown displayed (random timer)
     * - Material3 color scheme
     * - Interactive action buttons (pause/resume, reset, stop)
     * - Battery optimized (updates only every 1 second via chronometer)
     *
     * @param state Current timer state
     * @return Configured notification with chronometer and MD3 styling
     */
    private fun createTimerNotification(state: TimerState): Notification {
        val pendingIntent = createMainActivityIntent()
        val isPaused = state.status == TimerStatus.PAUSED
        val isComplete = state.status == TimerStatus.COMPLETE
        val isSilencedAlarm = state.status == TimerStatus.ALARM && state.isAlarmSilenced

        // Show the configured range instead of countdown (since it's a random timer)
        val minFormatted = formatSecondsToReadable(state.config.minSeconds)
        val maxFormatted = formatSecondsToReadable(state.config.maxSeconds)
        val rangeText = "$minFormatted - $maxFormatted"

        val title =
            when {
                isSilencedAlarm -> "Alarm Silenced"
                isComplete -> "Timer Complete!"
                isPaused -> "Timer Paused"
                else -> "Timer Running"
            }
        val text =
            if (isComplete || isSilencedAlarm) {
                "Went off after ${formatSecondsToReadable(state.targetDuration.inWholeSeconds.toInt())}"
            } else {
                "Goes off between $rangeText"
            }

        val builder =
            NotificationCompat
                .Builder(this, CHANNEL_TIMER)
                .setSmallIcon(R.drawable.ic_timer)
                .setContentTitle(title)
                .setContentText(text)
                .setSubText(if (state.config.hiddenMode) "Hidden Mode" else null)
                .setContentIntent(pendingIntent)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setCategory(NotificationCompat.CATEGORY_STOPWATCH)
                // Material Design 3 - Color accent for notification
                .setColor(getColor(R.color.accent_primary))
                .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)

        // Never show countdown — this is a random timer, revealing remaining time defeats the purpose
        builder.setShowWhen(false)

        if (isComplete || isSilencedAlarm) {
            // Complete or silenced alarm: Stop and Reset only
            builder.addAction(
                R.drawable.ic_stop,
                "Stop",
                createStopIntent(),
            )
            builder.addAction(
                R.drawable.ic_refresh,
                "Reset",
                createResetIntent(),
            )
        } else {
            // Running/Paused: Pause/Resume, Reset, Stop
            builder.addAction(
                if (isPaused) R.drawable.ic_play else R.drawable.ic_pause,
                if (isPaused) "Resume" else "Pause",
                if (isPaused) createResumeIntent() else createPauseIntent(),
            )
            builder.addAction(
                R.drawable.ic_refresh,
                "Reset",
                createResetIntent(),
            )
            builder.addAction(
                R.drawable.ic_stop,
                "Stop",
                createStopIntent(),
            )
        }

        return builder.build()
    }

    private fun formatSecondsToReadable(seconds: Int): String =
        when {
            seconds >= 60 -> {
                val mins = seconds / 60
                val secs = seconds % 60
                if (secs > 0) "${mins}m ${secs}s" else "${mins}m"
            }
            else -> "${seconds}s"
        }

    private fun createAlarmNotification(): Notification {
        val alarmTapIntent = createAlarmTapIntent()

        return NotificationCompat
            .Builder(this, CHANNEL_ALARM)
            .setSmallIcon(R.drawable.ic_alarm)
            .setContentTitle("Time's Up!")
            .setContentText("Your random timer has finished")
            .setContentIntent(alarmTapIntent)
            .setOngoing(true)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setFullScreenIntent(alarmTapIntent, true)
            .addAction(
                R.drawable.ic_stop,
                "Silence",
                createSilenceIntent(),
            ).addAction(
                R.drawable.ic_stop,
                "Stop",
                createStopFromAlarmNotificationIntent(),
            ).build()
    }

    private fun updateNotification(state: TimerState) {
        if (isAppInForeground) {
            removeForegroundNotification()
            return
        }

        val notification =
            if (state.shouldShowAlarmNotification) {
                createAlarmNotification()
            } else {
                createTimerNotification(state)
            }
        showOrUpdateForegroundNotification(notification)
    }

    private fun showOrUpdateForegroundNotification(notification: Notification) {
        if (isForegroundNotificationActive) {
            notificationManager.notify(NOTIFICATION_ID, notification)
            return
        }

        startForeground(NOTIFICATION_ID, notification)
        isForegroundNotificationActive = true
    }

    private fun removeForegroundNotification() {
        notificationManager.cancel(NOTIFICATION_ID)
        if (isForegroundNotificationActive) {
            stopForeground(STOP_FOREGROUND_REMOVE)
            isForegroundNotificationActive = false
        }
    }

    private fun createMainActivityIntent(): PendingIntent {
        val intent =
            Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
            }
        return PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private fun createAlarmTapIntent(): PendingIntent {
        val intent =
            Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
                putExtra(EXTRA_FROM_ALARM_NOTIFICATION, true)
            }
        return PendingIntent.getActivity(
            this,
            6,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private fun createStopIntent(): PendingIntent {
        val intent =
            Intent(this, TimerForegroundService::class.java).apply {
                action = ACTION_STOP
            }
        return PendingIntent.getService(
            this,
            1,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private fun createPauseIntent(): PendingIntent {
        val intent =
            Intent(this, TimerForegroundService::class.java).apply {
                action = ACTION_PAUSE
            }
        return PendingIntent.getService(
            this,
            3,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private fun createResumeIntent(): PendingIntent {
        val intent =
            Intent(this, TimerForegroundService::class.java).apply {
                action = ACTION_RESUME
            }
        return PendingIntent.getService(
            this,
            4,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private fun createResetIntent(): PendingIntent {
        val intent =
            Intent(this, TimerForegroundService::class.java).apply {
                action = ACTION_RESET
            }
        return PendingIntent.getService(
            this,
            5,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private fun createSilenceIntent(): PendingIntent {
        val intent =
            Intent(this, TimerForegroundService::class.java).apply {
                action = ACTION_SILENCE_ALARM
            }
        return PendingIntent.getService(
            this,
            7,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private fun createDismissIntent(): PendingIntent {
        val intent =
            Intent(this, TimerForegroundService::class.java).apply {
                action = ACTION_DISMISS_ALARM
            }
        return PendingIntent.getService(
            this,
            2,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private fun createStopFromAlarmNotificationIntent(): PendingIntent {
        // Open the app so the user lands back on the setup screen after stopping.
        val intent =
            Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
                putExtra(EXTRA_FROM_ALARM_STOP_ACTION, true)
            }

        return PendingIntent.getActivity(
            this,
            8,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private var alarmPlayer: MediaPlayer? = null
    private var fallbackRingtone: Ringtone? = null

    private fun playAlarmSound() {
        val state = _timerState.value ?: return
        if (!AlarmPlaybackPolicy.shouldRequestAudioFocus(state.status)) return
        val resourceId = resolveProSoundResId(this, state.config.soundType)
        val remoteFile = packStore.soundFile(state.config.soundType)

        // Request audio focus BEFORE playing alarm sound
        requestAlarmAudioFocus()

        try {
            alarmPlayer?.release()
            val alarmAttributes =
                AudioAttributes
                    .Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build()
            val player = MediaPlayer()
            player.setAudioAttributes(alarmAttributes)
            if (remoteFile != null) {
                player.setDataSource(remoteFile.absolutePath)
            } else {
                val afd =
                    resources.openRawResourceFd(resourceId)
                        ?: throw IllegalStateException("Could not open alarm sound resource")
                player.setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
                afd.close()
            }
            player.isLooping = true
            player.setVolume(state.config.volume, state.config.volume)
            player.prepare()
            player.start()
            alarmPlayer = player
            fallbackRingtone?.stop()
            fallbackRingtone = null
            Log.d("TimerService", "Playing alarm sound: ${state.config.soundType} at volume ${state.config.volume}")
        } catch (e: Exception) {
            Log.e("TimerService", "Failed to play alarm sound", e)
            val uri =
                RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                    ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            fallbackRingtone?.stop()
            fallbackRingtone =
                RingtoneManager.getRingtone(this, uri)?.apply {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                        isLooping = true
                    }
                    audioAttributes =
                        AudioAttributes
                            .Builder()
                            .setUsage(AudioAttributes.USAGE_ALARM)
                            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                            .build()
                    play()
                }
        }
    }

    private fun stopAlarmSound() {
        alarmPlayer?.stop()
        alarmPlayer?.release()
        alarmPlayer = null
        fallbackRingtone?.stop()
        fallbackRingtone = null
    }

    private fun startVibration() {
        val vib = vibrator ?: return

        if (!vib.hasVibrator()) {
            Log.w("TimerService", "Device does not have a vibrator")
            return
        }

        Log.d("TimerService", "Starting vibration")
        // Repeating pattern: wait 0ms, vibrate 500ms, pause 250ms, vibrate 500ms, pause 250ms, vibrate 500ms
        // The repeat index of 0 means repeat from the beginning
        val pattern = longArrayOf(0, 500, 250, 500, 250, 500)
        val alarmAttributes =
            AudioAttributes
                .Builder()
                .setUsage(AudioAttributes.USAGE_ALARM)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build()
        vib.vibrate(VibrationEffect.createWaveform(pattern, 0), alarmAttributes)
    }

    private fun stopVibration() {
        vibrator?.cancel()
    }

    // -- Audio Focus --

    private fun requestAlarmAudioFocus() {
        val audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        val focusRequest = AlarmAudioFocusRequestFactory.build()
        audioFocusRequest = focusRequest
        audioManager.requestAudioFocus(focusRequest)
    }

    private fun abandonAudioFocus() {
        audioFocusRequest?.let { request ->
            val audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
            audioManager.abandonAudioFocusRequest(request)
        }
        audioFocusRequest = null
    }

    // -- Screen Off (power button silence) --

    private fun registerScreenOffReceiver() {
        if (screenOffReceiver != null) return
        val receiver =
            ScreenOffReceiver {
                if (AlarmPlaybackPolicy.shouldSilenceOnScreenOff(_timerState.value?.status)) {
                    silenceAlarm()
                }
            }
        registerReceiver(receiver, IntentFilter(Intent.ACTION_SCREEN_OFF))
        screenOffReceiver = receiver
    }

    private fun unregisterScreenOffReceiver() {
        screenOffReceiver?.let {
            try {
                unregisterReceiver(it)
            } catch (_: IllegalArgumentException) {
                // Already unregistered
            }
        }
        screenOffReceiver = null
    }

    companion object {
        const val ACTION_START = "com.iganapolsky.randomtimer.START"
        const val ACTION_STOP = "com.iganapolsky.randomtimer.STOP"
        const val ACTION_PAUSE = "com.iganapolsky.randomtimer.PAUSE"
        const val ACTION_RESUME = "com.iganapolsky.randomtimer.RESUME"
        const val ACTION_RESET = "com.iganapolsky.randomtimer.RESET"
        const val ACTION_DISMISS_ALARM = "com.iganapolsky.randomtimer.DISMISS"
        const val ACTION_SILENCE_ALARM = "com.iganapolsky.randomtimer.SILENCE"
        const val ACTION_UPDATE_LOOP = "com.iganapolsky.randomtimer.UPDATE_LOOP"
        const val ACTION_UPDATE_VOICE = "com.iganapolsky.randomtimer.UPDATE_VOICE"
        const val ACTION_APP_STATE_CHANGED = "com.iganapolsky.randomtimer.APP_STATE"
        const val EXTRA_APP_IN_FOREGROUND = "app_in_foreground"
        const val EXTRA_TARGET_DURATION_MS = "target_duration_ms"
        const val EXTRA_REMAINING_DURATION_MS = "remaining_duration_ms"
        const val EXTRA_MIN_SECONDS = "min_seconds"
        const val EXTRA_MAX_SECONDS = "max_seconds"
        const val EXTRA_ALARM_DURATION = "alarm_duration"
        const val EXTRA_HIDDEN_MODE = "random_mode"
        const val EXTRA_REPEAT_ENABLED = "repeat_enabled"
        const val EXTRA_SOUND_TYPE = "sound_type"
        const val EXTRA_VOLUME = "volume"
        const val EXTRA_VIBRATION_ENABLED = "vibration_enabled"
        const val EXTRA_USE_EXTENDED_RANGE = "use_extended_range"
        const val EXTRA_VOICE_ENABLED = "voice_enabled"
        const val EXTRA_REPEAT_ROUNDS = "repeat_rounds"
        const val EXTRA_ROUND_COUNT = "round_count"
        const val EXTRA_FROM_ALARM_NOTIFICATION = "from_alarm_notification"
        const val EXTRA_FROM_ALARM_STOP_ACTION = "from_alarm_stop_action"

        private const val STOP_SOURCE_APP = "app"
        private const val STOP_SOURCE_NOTIFICATION = "notification"
        private const val STOP_SOURCE_TASK_REMOVED = "task_removed"
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_TIMER = "timer_progress"
        private const val CHANNEL_ALARM = "timer_alarm"
        private const val CHANNEL_MEDIA = "timer_media"
    }
}
