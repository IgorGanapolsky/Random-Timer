package com.iganapolsky.randomtimer.domain.usecase

import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import javax.inject.Inject
import kotlin.random.Random
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds

/**
 * Use case for starting a new timer with a random duration within the configured range.
 */
class StartTimerUseCase @Inject constructor(
    private val repository: TimerRepository,
    private val random: Random = Random.Default
) {
    suspend operator fun invoke(config: TimerConfig): TimerState {
        val randomDuration = generateRandomDuration(config.minDuration, config.maxDuration)

        val state = TimerState(
            config = config,
            targetDuration = randomDuration,
            remainingDuration = randomDuration,
            status = TimerStatus.RUNNING
        )

        repository.saveTimerConfig(config)
        repository.saveActiveTimer(state)

        return state
    }

    internal fun generateRandomDuration(min: Duration, max: Duration): Duration {
        if (min == max) return min

        val minMillis = min.inWholeMilliseconds
        val maxMillis = max.inWholeMilliseconds
        val randomMillis = random.nextLong(minMillis, maxMillis + 1)

        return randomMillis.milliseconds
    }
}
