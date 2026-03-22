package com.iganapolsky.randomtimer.domain.repository

import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import kotlinx.coroutines.flow.Flow

/**
 * Repository for timer configuration and state persistence.
 */
interface TimerRepository {
    /**
     * Get the saved timer configuration.
     */
    fun getTimerConfig(): Flow<TimerConfig>

    /**
     * Get the raw persisted timer configuration without Pro clamping.
     */
    suspend fun getRawTimerConfig(): TimerConfig

    /**
     * Save timer configuration for persistence.
     */
    suspend fun saveTimerConfig(config: TimerConfig)

    /**
     * Get the current active timer state, if any.
     */
    fun getActiveTimer(): Flow<TimerState?>

    /**
     * Save the active timer state for recovery after app restart.
     */
    suspend fun saveActiveTimer(state: TimerState)

    /**
     * Clear the active timer (when complete or cancelled).
     */
    suspend fun clearActiveTimer()
}
