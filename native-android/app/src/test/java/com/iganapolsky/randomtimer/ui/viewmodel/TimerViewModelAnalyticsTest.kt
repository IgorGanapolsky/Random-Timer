package com.iganapolsky.randomtimer.ui.viewmodel

import android.content.Context
import android.content.SharedPreferences
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.domain.SoundPreviewManager
import com.iganapolsky.randomtimer.service.AIVoiceCalloutManager
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
import io.mockk.every
import io.mockk.just
import io.mockk.mockk
import io.mockk.runs
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
    private lateinit var serviceController: TimerServiceController
    private lateinit var viewModel: TimerViewModel

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)

        val appContext = mockk<Context>()
        val mockPrefs = mockk<SharedPreferences>(relaxed = true)
        every { appContext.getSharedPreferences(any(), any()) } returns mockPrefs

        val repository = mockk<TimerRepository>()
        val startTimerUseCase = mockk<StartTimerUseCase>(relaxed = true)
        val soundPreviewManager = mockk<SoundPreviewManager>(relaxed = true)
        serviceController = mockk(relaxed = true)
        analyticsService = mockk(relaxed = true)
        val storeReviewManager = mockk<StoreReviewManager>(relaxed = true)
        val trainingStatsService = mockk<TrainingStatsService>(relaxed = true)
        val proManager = mockk<ProManager>(relaxed = true)
        every { proManager.entitlementLevel } returns MutableStateFlow(EntitlementLevel.ELITE)

        every { repository.getTimerConfig() } returns flowOf(TimerConfig.DEFAULT)
        coEvery { repository.clearActiveTimer() } just runs
        every { serviceController.bindService(any()) } just runs
        every { serviceController.unbindService(any()) } just runs

        viewModel =
            TimerViewModel(
                appContext = appContext,
                repository = repository,
                startTimerUseCase = startTimerUseCase,
                soundPreviewManager = soundPreviewManager,
                voiceCalloutManager = mockk<AIVoiceCalloutManager>(relaxed = true),
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
    fun `trackPaywallViewed tracks with entry point`() {
        viewModel.trackPaywallViewed("setup_upgrade_cta")
        verify {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_VIEWED,
                match { it["entry_point"] == "setup_upgrade_cta" },
            )
        }
    }

    @Test
    fun `trackPaywallDismissed tracks with entry point`() {
        viewModel.trackPaywallDismissed("setup_upgrade_cta")
        verify {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_DISMISSED,
                match { it["entry_point"] == "setup_upgrade_cta" },
            )
        }
    }

    @Test
    fun `cancelTimer does not track stop or abandoned directly`() {
        viewModel.cancelTimer()
        testDispatcher.scheduler.advanceUntilIdle()

        verify(exactly = 0) { analyticsService.track(AnalyticsEvents.TIMER_STOPPED, any()) }
        verify(exactly = 0) { analyticsService.track(AnalyticsEvents.TIMER_ABANDONED, any()) }
        verify(exactly = 1) { serviceController.stopTimer() }
    }

    private fun timerState(status: TimerStatus): TimerState =
        TimerState(
            config = TimerConfig.DEFAULT,
            targetDuration = 30.seconds,
            remainingDuration = 10.seconds,
            status = status,
        )
}
