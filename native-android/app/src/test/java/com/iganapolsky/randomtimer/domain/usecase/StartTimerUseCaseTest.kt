package com.iganapolsky.randomtimer.domain.usecase

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
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
import kotlin.random.Random
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

class StartTimerUseCaseTest {
    private lateinit var repository: TimerRepository
    private lateinit var useCase: StartTimerUseCase

    @Before
    fun setup() {
        repository = mockk()
        coEvery { repository.saveTimerConfig(any()) } just runs
        coEvery { repository.saveActiveTimer(any()) } just runs
    }

    @Test
    fun `generates random duration within range`() =
        runTest {
            val seededRandom = Random(42) // Deterministic for testing
            useCase = StartTimerUseCase(repository, seededRandom)

            val config =
                TimerConfig(
                    minSeconds = 300, // 5 minutes
                    maxSeconds = 300, // 5 minutes (same for predictable test)
                    alarmDuration = 10,
                    hiddenMode = false,
                    repeatEnabled = false,
                    soundType = SoundType.INTENSE,
                    volume = 0.5f,
                    vibrationEnabled = false,
                )

            val result = useCase(config)

            assertThat(result.targetDuration).isAtLeast(5.minutes)
            assertThat(result.targetDuration).isAtMost(5.minutes)
        }

    @Test
    fun `returns same duration when min equals max`() =
        runTest {
            useCase = StartTimerUseCase(repository)

            val config =
                TimerConfig(
                    minSeconds = 300, // 5 minutes
                    maxSeconds = 300, // 5 minutes
                    alarmDuration = 10,
                    hiddenMode = false,
                    repeatEnabled = false,
                    soundType = SoundType.INTENSE,
                    volume = 0.5f,
                    vibrationEnabled = false,
                )

            val result = useCase(config)

            assertThat(result.targetDuration).isEqualTo(5.minutes)
        }

    @Test
    fun `returns state with RUNNING status`() =
        runTest {
            useCase = StartTimerUseCase(repository)

            val result = useCase(TimerConfig.DEFAULT)

            assertThat(result.status).isEqualTo(TimerStatus.RUNNING)
        }

    @Test
    fun `remaining equals target at start`() =
        runTest {
            useCase = StartTimerUseCase(repository)

            val result = useCase(TimerConfig.DEFAULT)

            assertThat(result.remainingDuration).isEqualTo(result.targetDuration)
        }

    @Test
    fun `saves config to repository`() =
        runTest {
            useCase = StartTimerUseCase(repository)
            val config =
                TimerConfig(
                    minSeconds = 180, // 3 minutes
                    maxSeconds = 300, // 5 minutes (max allowed)
                    alarmDuration = 10,
                    hiddenMode = false,
                    repeatEnabled = false,
                    soundType = SoundType.INTENSE,
                    volume = 0.5f,
                    vibrationEnabled = false,
                )

            useCase(config)

            coVerify { repository.saveTimerConfig(config) }
        }

    @Test
    fun `saves active timer to repository`() =
        runTest {
            useCase = StartTimerUseCase(repository)

            useCase(TimerConfig.DEFAULT)

            coVerify { repository.saveActiveTimer(any()) }
        }

    @Test
    fun `generateRandomDuration produces varied results`() {
        useCase = StartTimerUseCase(repository)

        val results =
            (1..100)
                .map {
                    useCase.generateRandomDuration(1.minutes, 5.minutes) // Max is 5 min (300s)
                }.distinct()

        // Should have some variety (not all the same)
        assertThat(results.size).isGreaterThan(1)
    }

    @Test
    fun `generateRandomDuration respects boundaries`() {
        useCase = StartTimerUseCase(repository)
        val min = 30.seconds
        val max = 2.minutes

        repeat(100) {
            val duration = useCase.generateRandomDuration(min, max)
            assertThat(duration).isAtLeast(min)
            assertThat(duration).isAtMost(max)
        }
    }

    @Test
    fun `generateRandomDuration never picks zero when range spans at least one second`() {
        useCase = StartTimerUseCase(repository)
        val min = 0.seconds
        val max = 30.seconds

        repeat(200) {
            val duration = useCase.generateRandomDuration(min, max)
            assertThat(duration).isAtLeast(1.seconds)
            assertThat(duration).isAtMost(max)
        }
    }
}
