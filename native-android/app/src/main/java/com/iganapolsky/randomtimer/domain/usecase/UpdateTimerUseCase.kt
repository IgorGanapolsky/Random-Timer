package com.iganapolsky.randomtimer.domain.usecase

import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import javax.inject.Inject
import kotlin.time.Duration

/**
 * Use case for updating timer state as time progresses.
 */
class UpdateTimerUseCase
    @Inject
    constructor(
        private val repository: TimerRepository,
    ) {
        suspend operator fun invoke(
            currentState: TimerState,
            elapsedSinceLastTick: Duration,
        ): TimerState {
            val newRemaining =
                (currentState.remainingDuration - elapsedSinceLastTick)
                    .coerceAtLeast(Duration.ZERO)

            val newStatus = determineStatus(newRemaining, currentState.status)

            val newState =
                currentState.copy(
                    remainingDuration = newRemaining,
                    status = newStatus,
                )

            repository.saveActiveTimer(newState)
            return newState
        }

        internal fun determineStatus(
            remaining: Duration,
            currentStatus: TimerStatus,
        ): TimerStatus =
            when {
                remaining <= Duration.ZERO -> TimerStatus.COMPLETE
                currentStatus == TimerStatus.PAUSED -> TimerStatus.PAUSED
                else -> TimerStatus.RUNNING
            }
    }
