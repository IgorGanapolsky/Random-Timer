package com.iganapolsky.randomtimer.domain.usecase

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.just
import io.mockk.mockk
import io.mockk.runs
import kotlinx.coroutines.test.runTest
import org.junit.Before
import org.junit.Test
import kotlin.time.Duration
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

class UpdateTimerUseCaseTest {

    private lateinit var repository: TimerRepository
    private lateinit var useCase: UpdateTimerUseCase

    @Before
    fun setup() {
        repository = mockk()
        coEvery { repository.saveActiveTimer(any()) } just runs
        useCase = UpdateTimerUseCase(repository)
    }

    @Test
    fun `decrements remaining duration by elapsed time`() = runTest {
        val initialState = createRunningState(remaining = 2.minutes)

        val result = useCase(initialState, 1.seconds)

        assertThat(result.remainingDuration).isEqualTo(2.minutes - 1.seconds)
    }

    @Test
    fun `remaining does not go below zero`() = runTest {
        val initialState = createRunningState(remaining = 500.milliseconds)

        val result = useCase(initialState, 1.seconds)

        assertThat(result.remainingDuration).isEqualTo(Duration.ZERO)
    }

    @Test
    fun `transitions to WARNING under 30 seconds`() = runTest {
        val initialState = createRunningState(remaining = 31.seconds)

        val result = useCase(initialState, 2.seconds)

        assertThat(result.status).isEqualTo(TimerStatus.WARNING)
    }

    @Test
    fun `transitions to DANGER under 10 seconds`() = runTest {
        val initialState = createRunningState(remaining = 11.seconds, status = TimerStatus.WARNING)

        val result = useCase(initialState, 2.seconds)

        assertThat(result.status).isEqualTo(TimerStatus.DANGER)
    }

    @Test
    fun `transitions to COMPLETE at zero`() = runTest {
        val initialState = createRunningState(remaining = 1.seconds, status = TimerStatus.DANGER)

        val result = useCase(initialState, 1.seconds)

        assertThat(result.status).isEqualTo(TimerStatus.COMPLETE)
    }

    @Test
    fun `saves updated state to repository`() = runTest {
        val initialState = createRunningState(remaining = 5.minutes)

        useCase(initialState, 1.seconds)

        coVerify { repository.saveActiveTimer(any()) }
    }

    @Test
    fun `determineStatus returns RUNNING above 30 seconds`() {
        val status = useCase.determineStatus(31.seconds, TimerStatus.RUNNING)

        assertThat(status).isEqualTo(TimerStatus.RUNNING)
    }

    @Test
    fun `determineStatus returns WARNING at exactly 30 seconds`() {
        val status = useCase.determineStatus(30.seconds, TimerStatus.RUNNING)

        assertThat(status).isEqualTo(TimerStatus.WARNING)
    }

    @Test
    fun `determineStatus returns DANGER at exactly 10 seconds`() {
        val status = useCase.determineStatus(10.seconds, TimerStatus.WARNING)

        assertThat(status).isEqualTo(TimerStatus.DANGER)
    }

    @Test
    fun `determineStatus preserves PAUSED status`() {
        val status = useCase.determineStatus(2.minutes, TimerStatus.PAUSED)

        assertThat(status).isEqualTo(TimerStatus.PAUSED)
    }

    private fun createRunningState(
        remaining: Duration,
        status: TimerStatus = TimerStatus.RUNNING
    ): TimerState {
        return TimerState(
            config = TimerConfig.DEFAULT,
            targetDuration = 5.minutes,
            remainingDuration = remaining,
            status = status
        )
    }

    private val Int.milliseconds: Duration get() = Duration.parse("${this}ms")
}
