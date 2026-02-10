package com.iganapolsky.randomtimer.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.media.MediaPlayer
import android.media.Ringtone
import android.media.RingtoneManager
import android.util.Log
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.support.v4.media.session.MediaSessionCompat
import android.support.v4.media.session.PlaybackStateCompat
import androidx.core.app.NotificationCompat
import com.iganapolsky.randomtimer.MainActivity
import com.iganapolsky.randomtimer.R
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.ui.components.formatDuration
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
import kotlin.time.Duration.Companion.seconds

@AndroidEntryPoint
class TimerForegroundService : Service() {

    private val binder = LocalBinder()
    private val serviceScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var timerJob: Job? = null

    private val _timerState = MutableStateFlow<TimerState?>(null)
    val timerState: StateFlow<TimerState?> = _timerState.asStateFlow()

    private lateinit var notificationManager: NotificationManager
    private var isAppInForeground = false

    // Media session for Bluetooth/Android Auto alarm dismiss
    private var mediaSession: MediaSessionCompat? = null
    private var audioFocusRequest: AudioFocusRequest? = null

    inner class LocalBinder : Binder() {
        fun getService(): TimerForegroundService = this@TimerForegroundService
    }

    override fun onCreate() {
        super.onCreate()
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        createNotificationChannels()
        createMediaSession()
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.hasExtra(EXTRA_APP_IN_FOREGROUND) == true) {
            isAppInForeground = intent.getBooleanExtra(EXTRA_APP_IN_FOREGROUND, isAppInForeground)
        }
        when (intent?.action) {
            ACTION_APP_STATE_CHANGED -> {
                isAppInForeground = intent.getBooleanExtra(EXTRA_APP_IN_FOREGROUND, false)
            }
            ACTION_UPDATE_LOOP -> {
                val repeatEnabled = intent.getBooleanExtra(EXTRA_REPEAT_ENABLED, false)
                updateLoopSetting(repeatEnabled)
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
                        vibrationEnabled = vibrationEnabled
                    )
                }
            }
            ACTION_STOP -> stopTimer()
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
            val updatedConfig = current.config.copy(repeatEnabled = repeatEnabled)
            _timerState.value = current.copy(config = updatedConfig)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        deactivateMediaSession()
        mediaSession?.release()
        mediaSession = null
        stopAlarmSound()
        stopVibration()
        serviceScope.cancel()
    }

    override fun onTaskRemoved(rootIntent: Intent?) {
        super.onTaskRemoved(rootIntent)
        // User swiped app away from recents - stop everything
        stopAlarmSound()
        stopVibration()
        timerJob?.cancel()
        alarmCountdownJob?.cancel()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
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
        vibrationEnabled: Boolean
    ) {
        val config = TimerConfig(
            minSeconds = minSeconds,
            maxSeconds = maxSeconds,
            alarmDuration = alarmDuration,
            hiddenMode = hiddenMode,
            repeatEnabled = repeatEnabled,
            soundType = try { SoundType.valueOf(soundType) } catch (_: Exception) { SoundType.INTENSE },
            volume = volume,
            vibrationEnabled = vibrationEnabled
        )

        val initialState = TimerState(
            config = config,
            targetDuration = kotlin.time.Duration.parse("${targetMs}ms"),
            remainingDuration = kotlin.time.Duration.parse("${remainingMs}ms"),
            status = TimerStatus.RUNNING
        )

        startTimer(initialState)
    }

    private fun startTimer(initialState: TimerState) {
        _timerState.value = initialState
        startForeground(NOTIFICATION_ID, createTimerNotification(initialState))

        timerJob?.cancel()
        timerJob = serviceScope.launch {
            var state = initialState

            while (isActive && state.status != TimerStatus.COMPLETE) {
                delay(1000)

                val newRemaining = (state.remainingDuration - 1.seconds)
                    .coerceAtLeast(kotlin.time.Duration.ZERO)

                // Random timer - don't reveal warning/danger, just running until complete
                val newStatus = when {
                    newRemaining <= kotlin.time.Duration.ZERO -> TimerStatus.COMPLETE
                    else -> TimerStatus.RUNNING
                }

                // Update from current _timerState to preserve config changes
                // (e.g. loop toggle) made between ticks
                val current = _timerState.value ?: state
                state = current.copy(
                    remainingDuration = newRemaining,
                    status = newStatus
                )

                _timerState.value = state
                updateNotification(state)

                if (newStatus == TimerStatus.COMPLETE) {
                    triggerAlarm(state)
                }
            }
        }
    }

    private fun stopTimer() {
        timerJob?.cancel()
        alarmCountdownJob?.cancel()
        stopAlarmSound()
        stopVibration()
        _timerState.value = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun pauseTimer() {
        timerJob?.cancel()
        _timerState.value?.let { state ->
            if (state.status != TimerStatus.PAUSED) {
                _timerState.value = state.copy(status = TimerStatus.PAUSED)
                updateNotification(_timerState.value!!)
            }
        }
    }

    private fun resumeTimer() {
        _timerState.value?.let { state ->
            if (state.status == TimerStatus.PAUSED) {
                // Random timer - resume to running state (no warning/danger)
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
        notificationManager.cancel(NOTIFICATION_ID)
        deactivateMediaSession()
        stopAlarmSound()
        stopVibration()
        _timerState.value?.let { state ->
            val resetState = state.copy(
                remainingDuration = state.targetDuration,
                status = TimerStatus.RUNNING,
                alarmTimeRemaining = kotlin.time.Duration.ZERO,
                startedAt = System.currentTimeMillis()
            )
            startTimer(resetState)
        }
    }

    private fun dismissAlarm() {
        alarmCountdownJob?.cancel()
        deactivateMediaSession()
        stopAlarmSound()
        stopVibration()
        stopTimer()
    }

    private fun silenceAlarm() {
        // Stop sound/vibration but keep alarm state + countdown running
        // so the alarm screen stays visible in the UI
        deactivateMediaSession()
        stopAlarmSound()
        stopVibration()
    }

    private fun triggerAlarm(state: TimerState) {
        // Update status to ALARM
        _timerState.value = state.copy(
            status = TimerStatus.ALARM,
            alarmTimeRemaining = state.config.alarmDuration.seconds
        )

        // Activate media session so Bluetooth/Android Auto buttons can dismiss
        activateMediaSession()

        // Only show alarm notification if app is NOT in foreground
        if (!isAppInForeground) {
            val alarmNotification = createAlarmNotification()
            notificationManager.notify(NOTIFICATION_ID, alarmNotification)
        }

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
        alarmCountdownJob = serviceScope.launch {
            var remaining = durationSeconds
            while (isActive && remaining > 0) {
                delay(1000)
                remaining--

                // Update alarm time remaining in state
                _timerState.value?.let { current ->
                    _timerState.value = current.copy(
                        alarmTimeRemaining = remaining.seconds
                    )
                }
            }

            // Alarm duration finished - stop alarm and check for loop
            if (isActive) {
                deactivateMediaSession()
                stopAlarmSound()
                stopVibration()

                val currentState = _timerState.value
                if (currentState?.config?.repeatEnabled == true) {
                    // Auto-restart timer
                    restartTimerInternal()
                } else {
                    // Alarm duration finished — clean up service and notification
                    _timerState.value = null
                    stopForeground(STOP_FOREGROUND_REMOVE)
                    stopSelf()
                }
            }
        }
    }

    private fun restartTimerInternal() {
        val currentConfig = _timerState.value?.config ?: return

        // Generate new random duration
        val minMs = currentConfig.minSeconds * 1000L
        val maxMs = currentConfig.maxSeconds * 1000L
        val randomMs = kotlin.random.Random.nextLong(minMs, maxMs + 1)

        val newState = TimerState(
            config = currentConfig,
            targetDuration = kotlin.time.Duration.parse("${randomMs}ms"),
            remainingDuration = kotlin.time.Duration.parse("${randomMs}ms"),
            status = TimerStatus.RUNNING
        )

        startTimer(newState)
    }

    private fun createNotificationChannels() {
        // Timer progress channel (lock screen visible)
        val timerChannel = NotificationChannel(
            CHANNEL_TIMER,
            "Active Timer",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Shows timer countdown on lock screen"
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            setShowBadge(true)
        }

        // Alarm channel (high priority, no sound - we handle sound via Ringtone for better control)
        val alarmChannel = NotificationChannel(
            CHANNEL_ALARM,
            "Timer Alarm",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Alerts when timer completes"
            enableVibration(false) // We handle vibration separately
            setShowBadge(true)
            setSound(null, null) // No channel sound - we control sound via Ringtone
        }

        notificationManager.createNotificationChannels(listOf(timerChannel, alarmChannel))
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

        // Show the configured range instead of countdown (since it's a random timer)
        val minFormatted = formatSecondsToReadable(state.config.minSeconds)
        val maxFormatted = formatSecondsToReadable(state.config.maxSeconds)
        val rangeText = "$minFormatted - $maxFormatted"

        val builder = NotificationCompat.Builder(this, CHANNEL_TIMER)
            .setSmallIcon(R.drawable.ic_timer)
            .setContentTitle(if (isPaused) "Timer Paused" else "Timer Running")
            .setContentText("Goes off between $rangeText")
            .setSubText(if (state.config.hiddenMode) "Hidden Mode" else null)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setCategory(NotificationCompat.CATEGORY_STOPWATCH)
            // Material Design 3 - Color accent for notification
            .setColor(getColor(R.color.accent_primary))
            // Never show countdown in notification for random timer
            .setShowWhen(false)
            // Primary action: Pause/Resume
            .addAction(
                if (isPaused) R.drawable.ic_play else R.drawable.ic_pause,
                if (isPaused) "Resume" else "Pause",
                if (isPaused) createResumeIntent() else createPauseIntent()
            )

        // Reset action (always available)
        builder.addAction(
            R.drawable.ic_refresh,
            "Reset",
            createResetIntent()
        )

        // Stop action (always available)
        builder.addAction(
            R.drawable.ic_stop,
            "Stop",
            createStopIntent()
        )

        return builder.build()
    }

    private fun formatSecondsToReadable(seconds: Int): String {
        return when {
            seconds >= 60 -> {
                val mins = seconds / 60
                val secs = seconds % 60
                if (secs > 0) "${mins}m ${secs}s" else "${mins}m"
            }
            else -> "${seconds}s"
        }
    }

    private fun createAlarmNotification(): Notification {
        val alarmTapIntent = createAlarmTapIntent()

        return NotificationCompat.Builder(this, CHANNEL_ALARM)
            .setSmallIcon(R.drawable.ic_alarm)
            .setContentTitle("Time's Up!")
            .setContentText("Your random timer has finished")
            .setContentIntent(alarmTapIntent)
            .setOngoing(true)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setFullScreenIntent(alarmTapIntent, true)
            .addAction(
                R.drawable.ic_stop,
                "Dismiss",
                createDismissIntent()
            )
            .build()
    }

    private fun updateNotification(state: TimerState) {
        val notification = createTimerNotification(state)
        notificationManager.notify(NOTIFICATION_ID, notification)
    }

    private fun createMainActivityIntent(): PendingIntent {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        return PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private fun createAlarmTapIntent(): PendingIntent {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
            putExtra(EXTRA_FROM_ALARM_NOTIFICATION, true)
        }
        return PendingIntent.getActivity(
            this, 6, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private fun createStopIntent(): PendingIntent {
        val intent = Intent(this, TimerForegroundService::class.java).apply {
            action = ACTION_STOP
        }
        return PendingIntent.getService(
            this, 1, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private fun createPauseIntent(): PendingIntent {
        val intent = Intent(this, TimerForegroundService::class.java).apply {
            action = ACTION_PAUSE
        }
        return PendingIntent.getService(
            this, 3, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private fun createResumeIntent(): PendingIntent {
        val intent = Intent(this, TimerForegroundService::class.java).apply {
            action = ACTION_RESUME
        }
        return PendingIntent.getService(
            this, 4, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private fun createResetIntent(): PendingIntent {
        val intent = Intent(this, TimerForegroundService::class.java).apply {
            action = ACTION_RESET
        }
        return PendingIntent.getService(
            this, 5, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private fun createDismissIntent(): PendingIntent {
        val intent = Intent(this, TimerForegroundService::class.java).apply {
            action = ACTION_DISMISS_ALARM
        }
        return PendingIntent.getService(
            this, 2, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private var alarmPlayer: MediaPlayer? = null
    private var fallbackRingtone: Ringtone? = null

    private fun playAlarmSound() {
        val state = _timerState.value ?: return
        val resourceId = when (state.config.soundType) {
            SoundType.INTENSE -> R.raw.alarm
            SoundType.GENTLE -> R.raw.gentle_chime
        }

        try {
            alarmPlayer?.release()
            alarmPlayer = MediaPlayer.create(this, resourceId)?.apply {
                isLooping = true
                setVolume(state.config.volume, state.config.volume)
                start()
            }
            fallbackRingtone?.stop()
            fallbackRingtone = null
            Log.d("TimerService", "Playing alarm sound: ${state.config.soundType} at volume ${state.config.volume}")
        } catch (e: Exception) {
            Log.e("TimerService", "Failed to play alarm sound", e)
            // Fallback to system alarm
            val uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            fallbackRingtone?.stop()
            fallbackRingtone = RingtoneManager.getRingtone(this, uri)?.apply {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                    isLooping = true
                }
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
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val manager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
            manager.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }

        if (!vibrator.hasVibrator()) {
            Log.w("TimerService", "Device does not have a vibrator")
            return
        }

        Log.d("TimerService", "Starting vibration")
        // Repeating pattern: wait 0ms, vibrate 500ms, pause 250ms, vibrate 500ms, pause 250ms, vibrate 500ms
        // The repeat index of 0 means repeat from the beginning
        val pattern = longArrayOf(0, 500, 250, 500, 250, 500)
        vibrator.vibrate(VibrationEffect.createWaveform(pattern, 0))
    }

    private fun stopVibration() {
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val manager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
            manager.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }
        vibrator.cancel()
    }

    // -- Media Session for Bluetooth / Android Auto alarm dismiss --

    private fun createMediaSession() {
        mediaSession = MediaSessionCompat(this, "RandomTimer").apply {
            setCallback(object : MediaSessionCompat.Callback() {
                override fun onPlay() { dismissAlarm() }
                override fun onPause() { dismissAlarm() }
                override fun onStop() { dismissAlarm() }
            })
            // Don't activate yet — only activate when alarm is ringing
        }
    }

    private fun activateMediaSession() {
        mediaSession?.isActive = true

        // Set playback state to PLAYING so Bluetooth devices show pause button
        val playbackState = PlaybackStateCompat.Builder()
            .setActions(
                PlaybackStateCompat.ACTION_PLAY or
                PlaybackStateCompat.ACTION_PAUSE or
                PlaybackStateCompat.ACTION_STOP
            )
            .setState(PlaybackStateCompat.STATE_PLAYING, 0L, 1f)
            .build()
        mediaSession?.setPlaybackState(playbackState)

        // Request audio focus to route Bluetooth controls to this app
        val audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        val focusRequest = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build()
            )
            .build()
        audioFocusRequest = focusRequest
        audioManager.requestAudioFocus(focusRequest)

        Log.d("TimerService", "Media session activated for Bluetooth alarm dismiss")
    }

    private fun deactivateMediaSession() {
        mediaSession?.isActive = false

        val stoppedState = PlaybackStateCompat.Builder()
            .setState(PlaybackStateCompat.STATE_STOPPED, 0L, 0f)
            .build()
        mediaSession?.setPlaybackState(stoppedState)

        // Abandon audio focus
        audioFocusRequest?.let { request ->
            val audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
            audioManager.abandonAudioFocusRequest(request)
        }
        audioFocusRequest = null

        Log.d("TimerService", "Media session deactivated")
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
        const val EXTRA_FROM_ALARM_NOTIFICATION = "from_alarm_notification"

        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_TIMER = "timer_progress"
        private const val CHANNEL_ALARM = "timer_alarm"
    }
}
