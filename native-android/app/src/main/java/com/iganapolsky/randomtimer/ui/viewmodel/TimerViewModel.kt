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

        // Immediate in-memory config mirror to avoid DataStore propagation lag when starting.
        private var latestConfigOverride: TimerConfig? = null

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
            latestConfigOverride = newConfig
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                mapOf(
                    "min_duration" to newConfig.minSeconds,
                    "max_duration" to newConfig.maxSeconds,
                    "sound_type" to newConfig.soundType.name,
                    "repeat_enabled" to newConfig.repeatEnabled,
                ),
            )
            viewModelScope.launch {
                repository.saveTimerConfig(newConfig)
            }
        }

        fun startTimer() {
            stopSoundPreview()

            viewModelScope.launch {
                val effectiveConfig = latestConfigOverride ?: config.value
                val state = startTimerUseCase(effectiveConfig)
                _timerState.value = state
                serviceController.startTimer(state)
                analyticsService.track(
                    AnalyticsEvents.TIMER_STARTED,
                    mapOf(
                        "min_duration" to effectiveConfig.minSeconds,
                        "max_duration" to effectiveConfig.maxSeconds,
                        "target_duration" to state.targetDuration.inWholeSeconds,
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
            analyticsService.track(AnalyticsEvents.ALARM_DISMISSED)
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
            // Service owns the authoritative reset/reroll state. Avoid showing an optimistic
            // stale target locally before the service emits the updated timer state.
            serviceController.resetTimer()
        }

        fun updateLoopSetting(enabled: Boolean) {
            val updatedConfig = (latestConfigOverride ?: config.value).copy(repeatEnabled = enabled)
            latestConfigOverride = updatedConfig
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                mapOf(
                    "min_duration" to updatedConfig.minSeconds,
                    "max_duration" to updatedConfig.maxSeconds,
                    "sound_type" to updatedConfig.soundType.name,
                    "repeat_enabled" to updatedConfig.repeatEnabled,
                ),
            )
            viewModelScope.launch {
                repository.saveTimerConfig(updatedConfig)
                serviceController.updateLoop(enabled)
            }
        }

        fun trackScreen(screen: String) {
            analyticsService.screen(screen)
        }

        fun trackPaywallViewed(entryPoint: String) {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_VIEWED,
                mapOf(AnalyticsProperties.ENTRY_POINT to entryPoint),
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

        fun previewVoiceCallout() {
            soundPreviewManager.previewVoiceCallout()
        }

        fun previewDrillCommand() {
            soundPreviewManager.previewDrillCommand()
        }

        private fun stopSoundPreview() {
            soundPreviewManager.stop()
        }
    }
