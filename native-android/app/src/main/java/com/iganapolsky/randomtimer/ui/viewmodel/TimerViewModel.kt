package com.iganapolsky.randomtimer.ui.viewmodel

import android.content.ComponentName
import android.content.Context
import android.content.ServiceConnection
import android.os.IBinder
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsProperties
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.domain.SoundPreviewManager
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.model.VoiceGender
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.domain.usecase.StartTimerUseCase
import com.iganapolsky.randomtimer.review.StoreReviewManager
import com.iganapolsky.randomtimer.service.TimerForegroundService
import com.iganapolsky.randomtimer.service.TimerServiceController
import com.iganapolsky.randomtimer.stats.TrainingStatsService
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class TimerViewModel
    @Inject
    constructor(
        @ApplicationContext private val appContext: Context,
        private val repository: TimerRepository,
        private val startTimerUseCase: StartTimerUseCase,
        private val soundPreviewManager: SoundPreviewManager,
        private val serviceController: TimerServiceController,
        private val analyticsService: AnalyticsService,
        val storeReviewManager: StoreReviewManager,
        val trainingStatsService: TrainingStatsService,
        val proManager: ProManager,
    ) : ViewModel() {
        val totalSessions: Int get() = trainingStatsService.totalSessions
        val currentStreak: Int get() = trainingStatsService.currentStreak

        private val prefs = appContext.getSharedPreferences("onboarding", Context.MODE_PRIVATE)
        val hasCompletedFirstTimer: Boolean get() = prefs.getBoolean("hasCompletedFirstTimer", false)

        private fun markFirstTimerCompleted() {
            prefs.edit().putBoolean("hasCompletedFirstTimer", true).apply()
        }

        val config: StateFlow<TimerConfig> =
            repository
                .getTimerConfig()
                .stateIn(
                    scope = viewModelScope,
                    started = SharingStarted.WhileSubscribed(5000),
                    initialValue = TimerConfig.DEFAULT,
                )

        private val _timerState = MutableStateFlow<TimerState?>(null)
        val timerState: StateFlow<TimerState?> = _timerState

        /** Epoch millis when the alarm was triggered, used to compute alarm_response_time. */
        private var alarmTriggeredAtMs: Long = 0L

        private var service: TimerForegroundService? = null
        private var bound = false
        private var previousTimerStatus: TimerStatus? = null

        private val serviceConnection =
            object : ServiceConnection {
                override fun onServiceConnected(
                    name: ComponentName?,
                    binder: IBinder?,
                ) {
                    val localBinder = binder as TimerForegroundService.LocalBinder
                    service = localBinder.getService()
                    bound = true
                    viewModelScope.launch {
                        service?.timerState?.collect { state ->
                            onTimerStateObservedForAnalytics(previousTimerStatus, state)
                            previousTimerStatus = state?.status
                            _timerState.value = state
                        }
                    }
                }

                override fun onServiceDisconnected(name: ComponentName?) {
                    service = null
                    bound = false
                }
            }

        init {
            serviceController.bindService(serviceConnection)
        }

        override fun onCleared() {
            super.onCleared()
            if (bound) {
                serviceController.unbindService(serviceConnection)
                bound = false
            }
        }

        fun updateConfig(newConfig: TimerConfig) {
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                mapOf(
                    "min_duration" to newConfig.minSeconds,
                    "max_duration" to newConfig.maxSeconds,
                    "sound_type" to newConfig.soundType.name,
                    "repeat_enabled" to newConfig.repeatEnabled,
                    AnalyticsProperties.ENTITLEMENT_LEVEL to
                        proManager.entitlementLevel.value.name
                            .lowercase(),
                ),
            )
            viewModelScope.launch {
                repository.saveTimerConfig(newConfig)
            }
        }

        fun startTimer() {
            stopSoundPreview()

            viewModelScope.launch {
                val state = startTimerUseCase(config.value)
                _timerState.value = state
                serviceController.startTimer(state)
                analyticsService.track(
                    AnalyticsEvents.TIMER_STARTED,
                    mapOf(
                        "min_duration" to config.value.minSeconds,
                        "max_duration" to config.value.maxSeconds,
                        "target_duration" to state.targetDuration.inWholeSeconds,
                        AnalyticsProperties.ENTITLEMENT_LEVEL to
                            proManager.entitlementLevel.value.name
                                .lowercase(),
                    ),
                )
                analyticsService.trackFirstTimerConfiguredIfNeeded()
            }
        }

        fun cancelTimer() {
            viewModelScope.launch {
                repository.clearActiveTimer()
                _timerState.value = null
                serviceController.stopTimer()
            }
        }

        fun dismissAlarm() {
            val responseProps =
                buildMap<String, Any> {
                    if (alarmTriggeredAtMs > 0L) {
                        val responseTimeSec = (System.currentTimeMillis() - alarmTriggeredAtMs) / 1000.0
                        put(AnalyticsProperties.ALARM_RESPONSE_TIME, responseTimeSec)
                    }
                }
            analyticsService.track(AnalyticsEvents.ALARM_DISMISSED, responseProps.ifEmpty { null })
            viewModelScope.launch {
                repository.clearActiveTimer()
                _timerState.value = null
                serviceController.dismissAlarm()
            }
        }

        fun silenceAlarm() {
            serviceController.silenceAlarm()
        }

        fun pauseTimer() {
            analyticsService.track(AnalyticsEvents.TIMER_PAUSED)
            serviceController.pauseTimer()
        }

        fun resumeTimer() {
            analyticsService.track(AnalyticsEvents.TIMER_RESUMED)
            serviceController.resumeTimer()
        }

        fun restartTimer() {
            dismissAlarm()
            startTimer()
        }

        fun resetTimer() {
            analyticsService.track(AnalyticsEvents.TIMER_RESET)
            _timerState.value?.let { current ->
                _timerState.value =
                    current.copy(
                        remainingDuration = current.targetDuration,
                        status = TimerStatus.RUNNING,
                        alarmTimeRemaining = kotlin.time.Duration.ZERO,
                        startedAt = System.currentTimeMillis(),
                    )
            }
            serviceController.resetTimer()
        }

        fun updateLoopSetting(enabled: Boolean) {
            val current = _timerState.value?.config ?: config.value
            val updatedConfig =
                current.copy(
                    repeatEnabled = enabled,
                    useExtendedRange = current.useExtendedRange,
                    voiceEnabled = current.voiceEnabled,
                    repeatRounds = current.repeatRounds,
                )
            _timerState.value = _timerState.value?.copy(config = updatedConfig)
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                mapOf(
                    "min_duration" to updatedConfig.minSeconds,
                    "max_duration" to updatedConfig.maxSeconds,
                    "sound_type" to updatedConfig.soundType.name,
                    "repeat_enabled" to updatedConfig.repeatEnabled,
                    AnalyticsProperties.ENTITLEMENT_LEVEL to
                        proManager.entitlementLevel.value.name
                            .lowercase(),
                ),
            )
            viewModelScope.launch {
                repository.saveTimerConfig(updatedConfig)
                serviceController.updateLoop(enabled)
            }
        }

        fun updateVoiceSetting(enabled: Boolean) {
            val current = _timerState.value?.config ?: config.value
            val updatedConfig =
                current.copy(
                    voiceEnabled = enabled,
                    repeatEnabled = current.repeatEnabled,
                    useExtendedRange = current.useExtendedRange,
                    repeatRounds = current.repeatRounds,
                )
            _timerState.value = _timerState.value?.copy(config = updatedConfig)
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                mapOf(
                    "min_duration" to updatedConfig.minSeconds,
                    "max_duration" to updatedConfig.maxSeconds,
                    "sound_type" to updatedConfig.soundType.name,
                    "repeat_enabled" to updatedConfig.repeatEnabled,
                    "voice_callouts_enabled" to updatedConfig.voiceEnabled,
                    AnalyticsProperties.ENTITLEMENT_LEVEL to
                        proManager.entitlementLevel.value.name
                            .lowercase(),
                ),
            )
            viewModelScope.launch {
                repository.saveTimerConfig(updatedConfig)
                serviceController.updateVoiceEnabled(enabled)
            }
        }

        fun trackScreen(screen: String) {
            analyticsService.screen(screen)
        }

        fun trackScreenDwellTime(
            screen: String,
            durationSeconds: Double,
        ) {
            analyticsService.track(
                AnalyticsEvents.SCREEN_DWELL_TIME,
                mapOf(
                    AnalyticsProperties.SCREEN to screen,
                    "duration_seconds" to durationSeconds,
                ),
            )
        }

        fun trackPaywallViewed(entryPoint: String) {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_VIEWED,
                mapOf(AnalyticsProperties.ENTRY_POINT to entryPoint),
            )
        }

        fun trackVoiceGenderSelected(gender: VoiceGender) {
            analyticsService.track(
                AnalyticsEvents.VOICE_GENDER_SELECTED,
                mapOf(AnalyticsProperties.GENDER to gender.name.lowercase()),
            )
        }

        fun trackFeatureGateHit(feature: String) {
            analyticsService.track(
                AnalyticsEvents.FEATURE_GATE_HIT,
                mapOf(AnalyticsProperties.FEATURE to feature),
            )
        }

        fun trackPaywallGateFirstTimer(feature: String) {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_GATE_FIRST_TIMER,
                mapOf(AnalyticsProperties.FEATURE to feature),
            )
        }

        fun trackPaywallDismissed(entryPoint: String) {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_DISMISSED,
                mapOf(AnalyticsProperties.ENTRY_POINT to entryPoint),
            )
        }

        internal fun onTimerStateObservedForAnalytics(
            previousStatus: TimerStatus?,
            state: TimerState?,
        ) {
            val currentStatus = state?.status ?: return

            if (previousStatus != null && previousStatus != TimerStatus.ALARM && currentStatus == TimerStatus.ALARM) {
                alarmTriggeredAtMs = System.currentTimeMillis()
                analyticsService.track(
                    AnalyticsEvents.TIMER_COUNTDOWN_FINISHED,
                    mapOf("target_duration" to state.targetDuration.inWholeSeconds),
                )
                analyticsService.track(
                    AnalyticsEvents.ALARM_TRIGGERED,
                    mapOf("target_duration" to state.targetDuration.inWholeSeconds),
                )
            }

            if (previousStatus == TimerStatus.ALARM && currentStatus == TimerStatus.COMPLETE) {
                analyticsService.track(
                    AnalyticsEvents.TIMER_COMPLETED,
                    mapOf(
                        "target_duration" to state.targetDuration.inWholeSeconds,
                        AnalyticsProperties.ENTITLEMENT_LEVEL to
                            proManager.entitlementLevel.value.name
                                .lowercase(),
                    ),
                )
                analyticsService.trackFirstTimerCompletedIfNeeded()
                markFirstTimerCompleted()
            }
        }

        fun previewSound(soundType: SoundType) {
            soundPreviewManager.previewSound(soundType, config.value.volume)
        }

        fun previewVolume(volume: Float) {
            soundPreviewManager.previewVolume(config.value.soundType, volume)
        }

        fun previewCommandCue(gender: VoiceGender) {
            soundPreviewManager.previewCommandCue(gender)
        }

        private fun stopSoundPreview() {
            soundPreviewManager.stop()
        }
    }
