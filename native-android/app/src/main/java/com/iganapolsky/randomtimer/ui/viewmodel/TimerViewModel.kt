package com.iganapolsky.randomtimer.ui.viewmodel

import android.content.ComponentName
import android.content.ServiceConnection
import android.os.IBinder
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsProperties
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.analytics.PaywallExperimentVariants
import com.iganapolsky.randomtimer.analytics.SubscriptionFunnelSteps
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.monetization.ProSoundAccess
import com.iganapolsky.randomtimer.monetization.QualifiedTrainingPaywallAnalytics
import com.iganapolsky.randomtimer.monetization.RewardedAdCoordinator
import com.iganapolsky.randomtimer.monetization.RewardedAdPolicy
import com.iganapolsky.randomtimer.monetization.RewardedAdUnlockStore
import com.iganapolsky.randomtimer.domain.SoundPreviewManager
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.model.VoiceGender
import com.iganapolsky.randomtimer.domain.model.TrainingPreset
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.domain.usecase.StartTimerUseCase
import com.iganapolsky.randomtimer.review.StoreReviewManager
import com.iganapolsky.randomtimer.service.TimerForegroundService
import com.iganapolsky.randomtimer.service.TimerServiceController
import com.iganapolsky.randomtimer.stats.TrainingStatsService
import dagger.hilt.android.lifecycle.HiltViewModel
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
        private val repository: TimerRepository,
        private val startTimerUseCase: StartTimerUseCase,
        private val soundPreviewManager: SoundPreviewManager,
        private val serviceController: TimerServiceController,
        private val analyticsService: AnalyticsService,
        val storeReviewManager: StoreReviewManager,
        val trainingStatsService: TrainingStatsService,
        val proManager: ProManager,
        private val rewardedAdCoordinator: RewardedAdCoordinator,
        private val rewardedAdUnlockStore: RewardedAdUnlockStore,
    ) : ViewModel() {
        val totalSessions: Int get() = trainingStatsService.totalSessions
        val currentStreak: Int get() = trainingStatsService.currentStreak

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

        private val _proSoundTrialActive =
            MutableStateFlow(rewardedAdUnlockStore.hasActiveUnlock())
        val proSoundTrialActive: StateFlow<Boolean> = _proSoundTrialActive

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

        fun rewardedAdOfferVisible(): Boolean =
            RewardedAdPolicy.canOfferRewardedAd(
                rewardedAdsEnabled = analyticsService.rewardedAdsEnabled(),
                isPro = proManager.isPro.value,
            )

        fun requestRewardedProSoundUnlock(
            entryPoint: String = RewardedAdPolicy.ENTRY_SOUND_ARSENAL,
        ) {
            rewardedAdCoordinator.requestUnlock(
                entryPoint = entryPoint,
                rewardedAdsEnabled = analyticsService.rewardedAdsEnabled(),
                isPro = proManager.isPro.value,
                onUnlocked = { _proSoundTrialActive.value = true },
            )
        }

        fun updateConfig(newConfig: TimerConfig) {
            val previous = config.value
            trackSettingsChanges(previous, newConfig)
            if (
                ProSoundAccess.shouldConsumeTrialOnEquip(
                    isPro = proManager.isPro.value,
                    hasTrialUnlock = rewardedAdUnlockStore.hasActiveUnlock(),
                    previousSound = previous.soundType,
                    newSound = newConfig.soundType,
                )
            ) {
                rewardedAdUnlockStore.consumeUnlock()
                _proSoundTrialActive.value = false
            }
            viewModelScope.launch {
                repository.saveTimerConfig(newConfig)
            }
        }

        fun applyPresetAndStart(preset: TrainingPreset) {
            val newConfig = preset.applyTo(config.value)
            trackTrainingPresetApplied(
                presetId = preset.id,
                minSeconds = preset.minSeconds,
                maxSeconds = preset.maxSeconds,
            )
            viewModelScope.launch {
                repository.saveTimerConfig(newConfig)
                startTimer(newConfig)
            }
        }

        fun startTimer(overrideConfig: TimerConfig? = null) {
            stopSoundPreview()

            viewModelScope.launch {
                val configToUse = overrideConfig ?: config.value
                val state = startTimerUseCase(configToUse)
                _timerState.value = state
                serviceController.startTimer(state)
                analyticsService.track(
                    AnalyticsEvents.TIMER_STARTED,
                    mapOf(
                        "min_duration" to configToUse.minSeconds,
                        "max_duration" to configToUse.maxSeconds,
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
            trackSettingsChanges(current, updatedConfig)
            viewModelScope.launch {
                repository.saveTimerConfig(updatedConfig)
                serviceController.updateLoop(enabled)
            }
        }

        fun updateVoiceSetting(enabled: Boolean) {
            val current = _timerState.value?.config ?: config.value
            val effectiveEnabled = enabled && proManager.isPro.value
            val updatedConfig =
                current.copy(
                    voiceEnabled = effectiveEnabled,
                    repeatEnabled = current.repeatEnabled,
                    useExtendedRange = current.useExtendedRange,
                    repeatRounds = current.repeatRounds,
                )
            _timerState.value = _timerState.value?.copy(config = updatedConfig)
            trackSettingsChanges(current, updatedConfig)
            viewModelScope.launch {
                repository.saveTimerConfig(updatedConfig)
                serviceController.updateVoiceEnabled(effectiveEnabled)
            }
        }

        private fun trackSettingsChanges(
            previousConfig: TimerConfig,
            updatedConfig: TimerConfig,
        ) {
            val baseProperties =
                mapOf(
                    AnalyticsProperties.ENTITLEMENT_LEVEL to
                        proManager.entitlementLevel.value.name
                            .lowercase(),
                )

            fun emit(
                name: String,
                previousValue: Any,
                updatedValue: Any,
            ) {
                if (previousValue.toString() == updatedValue.toString()) return
                analyticsService.track(
                    AnalyticsEvents.SETTINGS_CHANGED,
                    baseProperties +
                        mapOf(
                            AnalyticsProperties.SETTING_NAME to name,
                            AnalyticsProperties.PREVIOUS_VALUE to previousValue,
                            AnalyticsProperties.SETTING_VALUE to updatedValue,
                        ),
                )
            }

            emit("min_seconds", previousConfig.minSeconds, updatedConfig.minSeconds)
            emit("max_seconds", previousConfig.maxSeconds, updatedConfig.maxSeconds)
            emit("alarm_duration", previousConfig.alarmDuration, updatedConfig.alarmDuration)
            emit("repeat_enabled", previousConfig.repeatEnabled, updatedConfig.repeatEnabled)
            emit("sound_type", previousConfig.soundType.name.lowercase(), updatedConfig.soundType.name.lowercase())
            emit("volume", previousConfig.volume, updatedConfig.volume)
            emit("vibration_enabled", previousConfig.vibrationEnabled, updatedConfig.vibrationEnabled)
            emit("use_extended_range", previousConfig.useExtendedRange, updatedConfig.useExtendedRange)
            emit("voice_callouts_enabled", previousConfig.voiceEnabled, updatedConfig.voiceEnabled)
            emit("voice_gender", previousConfig.voiceGender.name.lowercase(), updatedConfig.voiceGender.name.lowercase())
            emit("repeat_rounds", previousConfig.repeatRounds, updatedConfig.repeatRounds)
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

        fun resolvePaywallDefaultAnnualExperiment(onResolved: (Boolean) -> Unit) {
            analyticsService.reloadFeatureFlags {
                onResolved(analyticsService.paywallDefaultAnnualExperimentEnabled())
            }
        }

        fun paywallValueFramingVariant(): String = analyticsService.paywallValueFramingVariant()

        fun trackPaywallViewed(
            entryPoint: String,
            defaultAnnualExperiment: Boolean,
        ) {
            val experimentVariant =
                PaywallExperimentVariants.fromAnnualDefaultFlag(defaultAnnualExperiment)
            analyticsService.setPaywallSurfaceContext(entryPoint, experimentVariant)
            val framing = analyticsService.paywallValueFramingVariant()
            val props =
                mapOf(
                    AnalyticsProperties.ENTRY_POINT to entryPoint,
                    AnalyticsProperties.PAYWALL_EXPERIMENT_VARIANT to experimentVariant,
                    AnalyticsProperties.PAYWALL_VALUE_FRAMING_VARIANT to framing,
                )
            analyticsService.track(AnalyticsEvents.PAYWALL_VIEW, props)
            analyticsService.track(AnalyticsEvents.PAYWALL_VIEWED, props)
            analyticsService.trackSubscriptionFunnelStep(
                SubscriptionFunnelSteps.PAYWALL_VIEWED,
                emptyMap(),
            )
        }

        fun trackPaywallOfferSelected(
            entryPoint: String,
            productId: String,
            plan: String,
            selectionSource: String,
        ) {
            val framing = analyticsService.paywallValueFramingVariant()
            analyticsService.track(
                AnalyticsEvents.PAYWALL_OFFER_SELECT,
                mapOf(
                    AnalyticsProperties.ENTRY_POINT to entryPoint,
                    AnalyticsProperties.PRODUCT_ID to productId,
                    "plan" to plan,
                    AnalyticsProperties.PAYWALL_SELECTION_SOURCE to selectionSource,
                    AnalyticsProperties.PAYWALL_VALUE_FRAMING_VARIANT to framing,
                ),
            )
            analyticsService.trackSubscriptionFunnelStep(
                SubscriptionFunnelSteps.PAYWALL_PLAN_SELECTED,
                mapOf(
                    AnalyticsProperties.PRODUCT_ID to productId,
                    "plan" to plan,
                    AnalyticsProperties.PAYWALL_SELECTION_SOURCE to selectionSource,
                ),
            )
        }

        fun trackVoiceGenderSelected(gender: VoiceGender) {
            analyticsService.track(
                AnalyticsEvents.VOICE_GENDER_SELECTED,
                mapOf(AnalyticsProperties.GENDER to gender.name.lowercase()),
            )
        }

        fun trackTrainingPresetApplied(
            presetId: String,
            minSeconds: Int,
            maxSeconds: Int,
        ) {
            analyticsService.track(
                AnalyticsEvents.TRAINING_PRESET_APPLIED,
                mapOf(
                    AnalyticsProperties.PRESET_ID to presetId,
                    "min_duration" to minSeconds,
                    "max_duration" to maxSeconds,
                ),
            )
        }

        fun trackFeatureGateHit(feature: String) {
            analyticsService.track(
                AnalyticsEvents.FEATURE_GATE_HIT,
                mapOf(AnalyticsProperties.FEATURE to feature),
            )
        }

        fun trackQualifiedTrainingPaywallEligible(completedSessionCount: Int) {
            analyticsService.track(
                AnalyticsEvents.QUALIFIED_TRAINING_PAYWALL_ELIGIBLE,
                QualifiedTrainingPaywallAnalytics.eligibleProperties(completedSessionCount),
            )
        }

        fun trackPaywallDismissed(entryPoint: String) {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_DISMISSED,
                mapOf(
                    AnalyticsProperties.ENTRY_POINT to entryPoint,
                    AnalyticsProperties.PAYWALL_VALUE_FRAMING_VARIANT to
                        analyticsService.paywallValueFramingVariant(),
                ),
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
