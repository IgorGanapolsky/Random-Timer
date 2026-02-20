package com.iganapolsky.randomtimer.ui.viewmodel

import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.domain.SoundPreviewManager
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.domain.usecase.StartTimerUseCase
import com.iganapolsky.randomtimer.review.StoreReviewManager
import com.iganapolsky.randomtimer.service.TimerServiceController
import io.mockk.every
import io.mockk.just
import io.mockk.mockk
import io.mockk.runs
import io.mockk.verify
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
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
    private lateinit var viewModel: TimerViewModel

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)

        val repository = mockk<TimerRepository>()
        val startTimerUseCase = mockk<StartTimerUseCase>(relaxed = true)
        val soundPreviewManager = mockk<SoundPreviewManager>(relaxed = true)
        val serviceController = mockk<TimerServiceController>()
        analyticsService = mockk(relaxed = true)
        val storeReviewManager = mockk<StoreReviewManager>(relaxed = true)

        every { repository.getTimerConfig() } returns flowOf(TimerConfig.DEFAULT)
        every { serviceController.bindService(any()) } just runs
        every { serviceController.unbindService(any()) } just runs

        viewModel = TimerViewModel(
            repository = repository,
            startTimerUseCase = startTimerUseCase,
            soundPreviewManager = soundPreviewManager,
            serviceController = serviceController,
            analyticsService = analyticsService,
            storeReviewManager = storeReviewManager,
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
                match { it["target_duration"] == 30L },
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

    private fun timerState(status: TimerStatus): TimerState =
        TimerState(
            config = TimerConfig.DEFAULT,
            targetDuration = 30.seconds,
            remainingDuration = 10.seconds,
            status = status,
        )
}
