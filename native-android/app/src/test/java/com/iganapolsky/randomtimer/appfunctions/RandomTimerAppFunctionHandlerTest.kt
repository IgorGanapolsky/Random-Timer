package com.iganapolsky.randomtimer.appfunctions

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.domain.model.EntitlementLevel
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.model.VoiceGender
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.domain.usecase.StartTimerUseCase
import com.iganapolsky.randomtimer.service.TimerServiceController
import io.mockk.just
import io.mockk.mockk
import io.mockk.runs
import io.mockk.slot
import io.mockk.verify
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import org.junit.Before
import org.junit.Test
import kotlin.random.Random
import kotlin.time.Duration.Companion.seconds

class RandomTimerAppFunctionHandlerTest {
    private lateinit var repository: FakeTimerRepository
    private lateinit var serviceController: TimerServiceController
    private lateinit var analyticsService: AnalyticsService
    private lateinit var proManager: ProManager
    private lateinit var handler: RandomTimerAppFunctionHandler

    @Before
    fun setUp() {
        repository = FakeTimerRepository()
        serviceController = mockk(relaxed = true)
        analyticsService = mockk(relaxed = true)
        proManager = mockk(relaxed = true)
        io.mockk.every { proManager.entitlementLevel } returns MutableStateFlow(EntitlementLevel.ELITE)
        io.mockk.every { analyticsService.trackFirstTimerConfiguredIfNeeded() } just runs

        handler =
            RandomTimerAppFunctionHandler(
                startTimerUseCase = StartTimerUseCase(repository, Random(1)),
                repository = repository,
                serviceController = serviceController,
                analyticsService = analyticsService,
                proManager = proManager,
                configFactory = RandomTimerAppFunctionConfigFactory(),
            )
    }

    @Test
    fun `configureRandomTimer saves config and tracks settings`() =
        runBlocking {
            val result =
                handler.configureRandomTimer(
                    minSeconds = 20,
                    maxSeconds = 40,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = true,
                    voiceGender = "FEMALE",
                    hiddenMode = true,
                    repeatEnabled = false,
                    vibrationEnabled = true,
                )

            assertThat(result.status).isEqualTo("configured")
            assertThat(repository.savedConfig.voiceGender).isEqualTo(VoiceGender.FEMALE)
            assertThat(repository.savedConfig.voiceEnabled).isTrue()
            verify {
                analyticsService.track(
                    AnalyticsEvents.SETTINGS_CHANGED,
                    match {
                        it["entry_point"] == "app_function" &&
                            it["voice_gender"] == "FEMALE" &&
                            it["voice_callouts_enabled"] == true
                    },
                )
            }
        }

    @Test
    fun `startRandomTimer persists state starts service and tracks analytics`() =
        runBlocking {
            val stateSlot = slot<TimerState>()

            val result =
                handler.startRandomTimer(
                    minSeconds = 25,
                    maxSeconds = 25,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = true,
                    voiceGender = "FEMALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                )

            verify { serviceController.startTimer(capture(stateSlot)) }
            assertThat(stateSlot.captured.config.voiceGender).isEqualTo(VoiceGender.FEMALE)
            assertThat(stateSlot.captured.targetDuration.inWholeSeconds).isEqualTo(25)
            assertThat(repository.activeTimer?.config?.voiceGender).isEqualTo(VoiceGender.FEMALE)
            assertThat(result.status).isEqualTo("running")
            assertThat(result.targetDurationSeconds).isEqualTo(25)
            verify {
                analyticsService.track(
                    AnalyticsEvents.TIMER_STARTED,
                    match {
                        it["entry_point"] == "app_function" &&
                            it["target_duration"] == 25L
                    },
                )
            }
        }

    @Test
    fun `pause resume and stop act on active timer`() =
        runBlocking {
            repository.savedConfig = TimerConfig.DEFAULT.copy(voiceGender = VoiceGender.FEMALE)
            repository.activeTimer =
                TimerState(
                    config = repository.savedConfig,
                    targetDuration = 30.seconds,
                    remainingDuration = 12.seconds,
                    status = TimerStatus.RUNNING,
                )

            val pauseResult = handler.pauseTimer()
            val resumeResult = handler.resumeTimer()
            val stopResult = handler.stopTimer()

            assertThat(pauseResult.status).isEqualTo("paused")
            assertThat(resumeResult.status).isEqualTo("running")
            assertThat(stopResult.status).isEqualTo("stopped")
            assertThat(repository.activeTimer).isNull()
            verify { serviceController.pauseTimer() }
            verify { serviceController.resumeTimer() }
            verify { serviceController.stopTimer() }
        }

    @Test
    fun `pauseTimer returns idle result when no active timer exists`() =
        runBlocking {
            repository.activeTimer = null

            val result = handler.pauseTimer()

            assertThat(result.status).isEqualTo("idle")
            assertThat(result.message).contains("No active timer")
        }

    @Test
    fun `resumeTimer returns idle result when no active timer exists`() =
        runBlocking {
            repository.activeTimer = null

            val result = handler.resumeTimer()

            assertThat(result.status).isEqualTo("idle")
            assertThat(result.message).contains("No active timer")
        }

    @Test
    fun `stopTimer returns idle result when no active timer exists`() =
        runBlocking {
            repository.activeTimer = null

            val result = handler.stopTimer()

            assertThat(result.status).isEqualTo("idle")
            assertThat(result.message).contains("No active timer")
        }

    private class FakeTimerRepository : TimerRepository {
        var savedConfig: TimerConfig = TimerConfig.DEFAULT
        var activeTimer: TimerState? = null

        override fun getTimerConfig() = flowOf(savedConfig)

        override suspend fun saveTimerConfig(config: TimerConfig) {
            savedConfig = config
        }

        override fun getActiveTimer() = flowOf(activeTimer)

        override suspend fun saveActiveTimer(state: TimerState) {
            activeTimer = state
        }

        override suspend fun clearActiveTimer() {
            activeTimer = null
        }
    }
}
