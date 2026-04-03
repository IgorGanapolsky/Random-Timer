package com.iganapolsky.randomtimer.appfunctions

import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsProperties
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.domain.usecase.StartTimerUseCase
import com.iganapolsky.randomtimer.service.TimerServiceController
import javax.inject.Inject
import kotlinx.coroutines.flow.first

class RandomTimerAppFunctionHandler
    @Inject
    constructor(
        private val startTimerUseCase: StartTimerUseCase,
        private val repository: TimerRepository,
        private val serviceController: TimerServiceController,
        private val analyticsService: AnalyticsService,
        private val proManager: ProManager,
        private val configFactory: RandomTimerAppFunctionConfigFactory,
    ) {
        suspend fun configureRandomTimer(
            minSeconds: Int,
            maxSeconds: Int,
            alarmDuration: Int,
            soundType: String,
            voiceEnabled: Boolean,
            voiceGender: String,
            hiddenMode: Boolean,
            repeatEnabled: Boolean,
            vibrationEnabled: Boolean,
        ): TimerFunctionResult {
            val config =
                buildConfig(
                    minSeconds = minSeconds,
                    maxSeconds = maxSeconds,
                    alarmDuration = alarmDuration,
                    soundType = soundType,
                    voiceEnabled = voiceEnabled,
                    voiceGender = voiceGender,
                    hiddenMode = hiddenMode,
                    repeatEnabled = repeatEnabled,
                    vibrationEnabled = vibrationEnabled,
                )

            repository.saveTimerConfig(config)
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                config.analyticsProperties(),
            )
            analyticsService.trackFirstTimerConfiguredIfNeeded()

            return config.result(
                action = ACTION_CONFIGURE,
                status = STATUS_CONFIGURED,
                message = "Saved timer configuration.",
            )
        }

        suspend fun startRandomTimer(
            minSeconds: Int,
            maxSeconds: Int,
            alarmDuration: Int,
            soundType: String,
            voiceEnabled: Boolean,
            voiceGender: String,
            hiddenMode: Boolean,
            repeatEnabled: Boolean,
            vibrationEnabled: Boolean,
        ): TimerFunctionResult {
            val config =
                buildConfig(
                    minSeconds = minSeconds,
                    maxSeconds = maxSeconds,
                    alarmDuration = alarmDuration,
                    soundType = soundType,
                    voiceEnabled = voiceEnabled,
                    voiceGender = voiceGender,
                    hiddenMode = hiddenMode,
                    repeatEnabled = repeatEnabled,
                    vibrationEnabled = vibrationEnabled,
                )

            val state = startTimerUseCase(config)
            serviceController.startTimer(state)
            analyticsService.track(
                AnalyticsEvents.TIMER_STARTED,
                config.analyticsProperties() +
                    mapOf("target_duration" to state.targetDuration.inWholeSeconds),
            )
            analyticsService.trackFirstTimerConfiguredIfNeeded()

            return config.result(
                action = ACTION_START,
                status = STATUS_RUNNING,
                message = "Started random timer.",
                targetDurationSeconds = state.targetDuration.inWholeSeconds.toInt(),
            )
        }

        suspend fun pauseTimer(): TimerFunctionResult {
            val activeTimer = repository.getActiveTimer().first()
                ?: return idleResult(ACTION_PAUSE, "No active timer to pause.")

            analyticsService.track(
                AnalyticsEvents.TIMER_PAUSED,
                mapOf(AnalyticsProperties.ENTRY_POINT to ENTRY_POINT),
            )
            serviceController.pauseTimer()
            return activeTimer.config.result(
                action = ACTION_PAUSE,
                status = STATUS_PAUSED,
                message = "Paused active timer.",
            )
        }

        suspend fun resumeTimer(): TimerFunctionResult {
            val activeTimer = repository.getActiveTimer().first()
                ?: return idleResult(ACTION_RESUME, "No active timer to resume.")

            analyticsService.track(
                AnalyticsEvents.TIMER_RESUMED,
                mapOf(AnalyticsProperties.ENTRY_POINT to ENTRY_POINT),
            )
            serviceController.resumeTimer()
            return activeTimer.config.result(
                action = ACTION_RESUME,
                status = STATUS_RUNNING,
                message = "Resumed active timer.",
            )
        }

        suspend fun stopTimer(): TimerFunctionResult {
            val activeTimer = repository.getActiveTimer().first()
                ?: return idleResult(ACTION_STOP, "No active timer to stop.")

            repository.clearActiveTimer()
            serviceController.stopTimer()
            return activeTimer.config.result(
                action = ACTION_STOP,
                status = STATUS_STOPPED,
                message = "Stopped active timer.",
            )
        }

        private fun buildConfig(
            minSeconds: Int,
            maxSeconds: Int,
            alarmDuration: Int,
            soundType: String,
            voiceEnabled: Boolean,
            voiceGender: String,
            hiddenMode: Boolean,
            repeatEnabled: Boolean,
            vibrationEnabled: Boolean,
        ): TimerConfig =
            configFactory.create(
                minSeconds = minSeconds,
                maxSeconds = maxSeconds,
                alarmDuration = alarmDuration,
                soundType = soundType,
                voiceEnabled = voiceEnabled,
                voiceGender = voiceGender,
                hiddenMode = hiddenMode,
                repeatEnabled = repeatEnabled,
                vibrationEnabled = vibrationEnabled,
                entitlementLevel = proManager.entitlementLevel.value,
            )

        private fun TimerConfig.analyticsProperties(): Map<String, Any> =
            mapOf(
                AnalyticsProperties.ENTRY_POINT to ENTRY_POINT,
                AnalyticsProperties.ENTITLEMENT_LEVEL to entitlementLevelName(),
                "min_duration" to minSeconds,
                "max_duration" to maxSeconds,
                "alarm_duration" to alarmDuration,
                "sound_type" to soundType.name,
                "hidden_mode" to hiddenMode,
                "repeat_enabled" to repeatEnabled,
                "vibration_enabled" to vibrationEnabled,
                "voice_callouts_enabled" to voiceEnabled,
                "voice_gender" to voiceGender.name,
            )

        private fun TimerConfig.result(
            action: String,
            status: String,
            message: String,
            targetDurationSeconds: Int = 0,
        ): TimerFunctionResult =
            TimerFunctionResult(
                action = action,
                status = status,
                message = message,
                entitlementLevel = entitlementLevelName(),
                minSeconds = minSeconds,
                maxSeconds = maxSeconds,
                alarmDuration = alarmDuration,
                targetDurationSeconds = targetDurationSeconds,
                soundType = soundType.name,
                voiceEnabled = voiceEnabled,
                voiceGender = voiceGender.name,
                hiddenMode = hiddenMode,
                repeatEnabled = repeatEnabled,
                vibrationEnabled = vibrationEnabled,
            )

        private fun idleResult(
            action: String,
            message: String,
        ): TimerFunctionResult =
            TimerFunctionResult(
                action = action,
                status = STATUS_IDLE,
                message = message,
                entitlementLevel = entitlementLevelName(),
                soundType = "",
                voiceGender = "",
            )

        private fun entitlementLevelName(): String = proManager.entitlementLevel.value.name.lowercase()

        companion object {
            private const val ENTRY_POINT = "app_function"
            private const val ACTION_CONFIGURE = "configure_random_timer"
            private const val ACTION_START = "start_random_timer"
            private const val ACTION_PAUSE = "pause_timer"
            private const val ACTION_RESUME = "resume_timer"
            private const val ACTION_STOP = "stop_timer"
            private const val STATUS_CONFIGURED = "configured"
            private const val STATUS_IDLE = "idle"
            private const val STATUS_PAUSED = "paused"
            private const val STATUS_RUNNING = "running"
            private const val STATUS_STOPPED = "stopped"
        }
    }
