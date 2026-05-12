package com.iganapolsky.randomtimer.ui.viewmodel

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsProperties
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.analytics.SubscriptionFunnelSteps
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.domain.SoundPreviewManager
import com.iganapolsky.randomtimer.domain.model.EntitlementLevel
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.domain.usecase.StartTimerUseCase
import com.iganapolsky.randomtimer.review.StoreReviewManager
import com.iganapolsky.randomtimer.service.TimerServiceController
import com.iganapolsky.randomtimer.stats.TrainingStatsService
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.just
import io.mockk.mockk
import io.mockk.runs
import io.mockk.slot
import io.mockk.verify
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Before
import org.junit.Test
import kotlin.time.Duration.Companion.seconds

@OptIn(ExperimentalCoroutinesApi::class)
class TimerViewModelAnalyticsTest {
    private val testDispatcher = StandardTestDispatcher()

    private lateinit var analyticsService: AnalyticsService
    private lateinit var repository: TimerRepository
    private lateinit var serviceController: TimerServiceController
    private lateinit var viewModel: TimerViewModel
    private lateinit var configFlow: MutableStateFlow<TimerConfig>

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)

        repository = mockk<TimerRepository>()
        val startTimerUseCase = mockk<StartTimerUseCase>(relaxed = true)
        val soundPreviewManager = mockk<SoundPreviewManager>(relaxed = true)
        serviceController = mockk(relaxed = true)
        analyticsService = mockk(relaxed = true)
        every { analyticsService.paywallValueFramingVariant() } returns "control"
        val storeReviewManager = mockk<StoreReviewManager>(relaxed = true)
        val trainingStatsService = mockk<TrainingStatsService>(relaxed = true)
        val proManager = mockk<ProManager>(relaxed = true)
        every { proManager.entitlementLevel } returns MutableStateFlow(EntitlementLevel.ELITE)
        every { proManager.isPro } returns MutableStateFlow(true)

        configFlow = MutableStateFlow(TimerConfig.DEFAULT)
        every { repository.getTimerConfig() } returns configFlow
        coEvery { repository.saveTimerConfig(any()) } just runs
        coEvery { repository.clearActiveTimer() } just runs
        every { serviceController.bindService(any()) } just runs
        every { serviceController.unbindService(any()) } just runs

        viewModel =
            TimerViewModel(
                repository = repository,
                startTimerUseCase = startTimerUseCase,
                soundPreviewManager = soundPreviewManager,
                serviceController = serviceController,
                analyticsService = analyticsService,
                storeReviewManager = storeReviewManager,
                trainingStatsService = trainingStatsService,
                proManager = proManager,
            )
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `tracks alarm_triggered when state transitions into alarm`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.RUNNING,
            state = timerState(TimerStatus.ALARM),
        )

        verify {
            analyticsService.track(
                AnalyticsEvents.ALARM_TRIGGERED,
                match { it["target_duration"] == 30L },
            )
        }
    }

    @Test
    fun `tracks timer_completed when state transitions from alarm to complete`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.ALARM,
            state = timerState(TimerStatus.COMPLETE),
        )

        verify {
            analyticsService.track(
                AnalyticsEvents.TIMER_COMPLETED,
                match {
                    it["target_duration"] == 30L &&
                        it["entitlement_level"] == "elite"
                },
            )
        }
    }

    @Test
    fun `does not retrack alarm when alarm status repeats`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.ALARM,
            state = timerState(TimerStatus.ALARM),
        )

        verify(exactly = 0) { analyticsService.track(AnalyticsEvents.ALARM_TRIGGERED, any()) }
        verify(exactly = 0) { analyticsService.track(AnalyticsEvents.TIMER_COMPLETED, any()) }
    }

    @Test
    fun `trackScreen delegates to analytics screen`() {
        viewModel.trackScreen("Timer Setup")
        verify { analyticsService.screen("Timer Setup") }
    }

    @Test
    fun `trackPaywallViewed tracks with entry point and experiment variant`() {
        viewModel.trackPaywallViewed("sound_arsenal_gate", defaultAnnualExperiment = false)
        verify {
            analyticsService.setPaywallSurfaceContext("sound_arsenal_gate", "monthly_default")
        }
        verify {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_VIEW,
                match {
                    it["entry_point"] == "sound_arsenal_gate" &&
                        it["paywall_experiment_variant"] == "monthly_default" &&
                        it["paywall_value_framing_variant"] == "control"
                },
            )
        }
        verify {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_VIEWED,
                match {
                    it["entry_point"] == "sound_arsenal_gate" &&
                        it["paywall_experiment_variant"] == "monthly_default" &&
                        it["paywall_value_framing_variant"] == "control"
                },
            )
        }
        verify {
            analyticsService.trackSubscriptionFunnelStep(
                SubscriptionFunnelSteps.PAYWALL_VIEWED,
                match { it.isEmpty() },
            )
        }
    }

    @Test
    fun `trackPaywallDismissed tracks with entry point`() {
        viewModel.trackPaywallDismissed("sound_arsenal_gate")
        verify {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_DISMISSED,
                match {
                    it["entry_point"] == "sound_arsenal_gate" &&
                        it["paywall_value_framing_variant"] == "control"
                },
            )
        }
    }

    @Test
    fun `trackPaywallOfferSelected includes selection source`() {
        viewModel.trackPaywallOfferSelected(
            entryPoint = "range_gate",
            productId = ProManager.ELITE_PRODUCT_ID,
            plan = "annual",
            selectionSource = "primary_cta",
        )

        verify {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_OFFER_SELECT,
                match {
                    it["entry_point"] == "range_gate" &&
                        it["product_id"] == ProManager.ELITE_PRODUCT_ID &&
                        it["plan"] == "annual" &&
                        it["paywall_selection_source"] == "primary_cta" &&
                        it["paywall_value_framing_variant"] == "control"
                },
            )
        }
        verify {
            analyticsService.trackSubscriptionFunnelStep(
                SubscriptionFunnelSteps.PAYWALL_PLAN_SELECTED,
                match {
                    it["product_id"] == ProManager.ELITE_PRODUCT_ID &&
                        it["plan"] == "annual" &&
                        it["paywall_selection_source"] == "primary_cta"
                },
            )
        }
    }

    @Test
    fun `updateConfig emits per-setting analytics with setting_name`() {
        val updated = TimerConfig.DEFAULT.copy(minSeconds = 10, maxSeconds = 45, voiceEnabled = true)

        viewModel.updateConfig(updated)
        testDispatcher.scheduler.advanceUntilIdle()

        verify {
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                match {
                    it[AnalyticsProperties.SETTING_NAME] == "min_seconds" &&
                        it[AnalyticsProperties.PREVIOUS_VALUE] == 5 &&
                        it[AnalyticsProperties.SETTING_VALUE] == 10
                },
            )
        }
        verify {
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                match {
                    it[AnalyticsProperties.SETTING_NAME] == "max_seconds" &&
                        it[AnalyticsProperties.PREVIOUS_VALUE] == 30 &&
                        it[AnalyticsProperties.SETTING_VALUE] == 45
                },
            )
        }
        verify {
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                match {
                    it[AnalyticsProperties.SETTING_NAME] == "voice_callouts_enabled" &&
                        it[AnalyticsProperties.PREVIOUS_VALUE] == false &&
                        it[AnalyticsProperties.SETTING_VALUE] == true
                },
            )
        }
    }

    @Test
    fun `recordCompletion not called after alarm to complete transition — service owns review eligibility`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.ALARM,
            state = timerState(TimerStatus.COMPLETE),
        )

        verify(exactly = 0) { viewModel.storeReviewManager.recordCompletion() }
    }

    @Test
    fun `recordCompletion NOT called when transitioning into alarm — too early for review`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.RUNNING,
            state = timerState(TimerStatus.ALARM),
        )

        verify(exactly = 0) { viewModel.storeReviewManager.recordCompletion() }
    }

    @Test
    fun `cancelTimer does not track stop or abandoned directly`() {
        viewModel.cancelTimer()
        testDispatcher.scheduler.advanceUntilIdle()

        verify(exactly = 0) { analyticsService.track(AnalyticsEvents.TIMER_STOPPED, any()) }
        verify(exactly = 0) { analyticsService.track(AnalyticsEvents.TIMER_ABANDONED, any()) }
        verify(exactly = 1) { serviceController.stopTimer() }
    }

    @Test
    fun `updateVoiceSetting preserves live loop configuration while timer is active`() {
        configFlow.value = TimerConfig.DEFAULT.copy(repeatEnabled = false, voiceEnabled = false, repeatRounds = 0)
        val liveState =
            timerState(TimerStatus.RUNNING).copy(
                config = TimerConfig.DEFAULT.copy(repeatEnabled = true, voiceEnabled = false, repeatRounds = 3),
            )
        viewModel.setActiveTimerStateForTest(liveState)
        val savedConfig = slot<TimerConfig>()

        viewModel.updateVoiceSetting(enabled = true)
        testDispatcher.scheduler.advanceUntilIdle()

        assertThat(
            viewModel.timerState.value
                ?.config
                ?.voiceEnabled,
        ).isTrue()
        assertThat(
            viewModel.timerState.value
                ?.config
                ?.repeatEnabled,
        ).isTrue()
        assertThat(
            viewModel.timerState.value
                ?.config
                ?.repeatRounds,
        ).isEqualTo(3)
        coVerify { repository.saveTimerConfig(capture(savedConfig)) }
        assertThat(savedConfig.captured.voiceEnabled).isTrue()
        assertThat(savedConfig.captured.repeatEnabled).isTrue()
        assertThat(savedConfig.captured.repeatRounds).isEqualTo(3)
        verify { serviceController.updateVoiceEnabled(true) }
    }

    @Test
    fun `updateLoopSetting preserves live voice configuration while timer is active`() {
        configFlow.value = TimerConfig.DEFAULT.copy(repeatEnabled = false, voiceEnabled = false, repeatRounds = 0)
        val liveState =
            timerState(TimerStatus.RUNNING).copy(
                config = TimerConfig.DEFAULT.copy(repeatEnabled = false, voiceEnabled = true, repeatRounds = 2),
            )
        viewModel.setActiveTimerStateForTest(liveState)
        val savedConfig = slot<TimerConfig>()

        viewModel.updateLoopSetting(enabled = true)
        testDispatcher.scheduler.advanceUntilIdle()

        assertThat(
            viewModel.timerState.value
                ?.config
                ?.repeatEnabled,
        ).isTrue()
        assertThat(
            viewModel.timerState.value
                ?.config
                ?.voiceEnabled,
        ).isTrue()
        assertThat(
            viewModel.timerState.value
                ?.config
                ?.repeatRounds,
        ).isEqualTo(2)
        coVerify { repository.saveTimerConfig(capture(savedConfig)) }
        assertThat(savedConfig.captured.repeatEnabled).isTrue()
        assertThat(savedConfig.captured.voiceEnabled).isTrue()
        assertThat(savedConfig.captured.repeatRounds).isEqualTo(2)
        verify { serviceController.updateLoop(true) }
    }

    private fun timerState(status: TimerStatus): TimerState =
        TimerState(
            config = TimerConfig.DEFAULT,
            targetDuration = 30.seconds,
            remainingDuration = 10.seconds,
            status = status,
        )

    private fun TimerViewModel.setActiveTimerStateForTest(state: TimerState?) {
        val field = TimerViewModel::class.java.getDeclaredField("_timerState")
        field.isAccessible = true
        @Suppress("UNCHECKED_CAST")
        val timerState = field.get(this) as MutableStateFlow<TimerState?>
        timerState.value = state
    }
}
