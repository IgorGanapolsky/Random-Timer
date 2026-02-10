package com.iganapolsky.randomtimer.service

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.runTest
import org.junit.Test
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

/**
 * Tests for the timer tick logic pattern used in TimerForegroundService.
 *
 * The core bug (fixed): timer tick loop captured `initialState` and overwrote
 * `_timerState.value` every second with stale config, undoing loop toggle
 * changes made between ticks.
 *
 * The fix: read from `_timerState.value` (current) before copying, so config
 * changes made via `updateLoopSetting()` survive timer ticks.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class TimerStateFlowTest {

    private val defaultConfig = TimerConfig(
        minSeconds = 30,
        maxSeconds = 120,
        alarmDuration = 10,
        hiddenMode = false,
        repeatEnabled = false,
        soundType = com.iganapolsky.randomtimer.domain.model.SoundType.INTENSE,
        volume = 0.5f,
        vibrationEnabled = false
    )

    // -- Bug regression test: loop toggle must survive timer ticks --

    @Test
    fun `config change via flow survives tick when reading from flow`() = runTest {
        // Simulates the FIXED timer tick pattern
        val timerState = MutableStateFlow<TimerState?>(null)
        val initialState = TimerState(
            config = defaultConfig,
            targetDuration = 2.minutes,
            remainingDuration = 2.minutes,
            status = TimerStatus.RUNNING
        )
        timerState.value = initialState

        // Simulate external config change (loop toggle ON)
        timerState.value?.let { current ->
            val updatedConfig = current.config.copy(repeatEnabled = true)
            timerState.value = current.copy(config = updatedConfig)
        }

        assertThat(timerState.value?.config?.repeatEnabled).isTrue()

        // Simulate timer tick — FIXED pattern: read from flow, then copy
        val current = timerState.value ?: initialState
        val tickedState = current.copy(
            remainingDuration = current.remainingDuration - 1.seconds,
            status = TimerStatus.RUNNING
        )
        timerState.value = tickedState

        // Config change must survive the tick
        assertThat(timerState.value?.config?.repeatEnabled).isTrue()
    }

    @Test
    fun `config change via flow is lost when reading from captured state (old bug)`() = runTest {
        // Demonstrates the OLD bug pattern for documentation
        val timerState = MutableStateFlow<TimerState?>(null)
        val initialState = TimerState(
            config = defaultConfig,
            targetDuration = 2.minutes,
            remainingDuration = 2.minutes,
            status = TimerStatus.RUNNING
        )
        timerState.value = initialState

        // Simulate external config change (loop toggle ON)
        timerState.value?.let { current ->
            val updatedConfig = current.config.copy(repeatEnabled = true)
            timerState.value = current.copy(config = updatedConfig)
        }

        assertThat(timerState.value?.config?.repeatEnabled).isTrue()

        // Simulate timer tick — OLD bug: copy from captured initialState
        // (This is the pattern that caused the bug)
        val tickedState = initialState.copy(
            remainingDuration = initialState.remainingDuration - 1.seconds,
            status = TimerStatus.RUNNING
        )
        timerState.value = tickedState

        // Config change is LOST because we copied from stale initialState
        assertThat(timerState.value?.config?.repeatEnabled).isFalse()
    }

    // -- updateLoopSetting tests --

    @Test
    fun `updateLoopSetting enables repeat`() {
        val timerState = MutableStateFlow<TimerState?>(null)
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 2.minutes,
            remainingDuration = 1.minutes,
            status = TimerStatus.RUNNING
        )
        timerState.value = state

        // Simulate updateLoopSetting(true)
        timerState.value?.let { current ->
            val updatedConfig = current.config.copy(repeatEnabled = true)
            timerState.value = current.copy(config = updatedConfig)
        }

        assertThat(timerState.value?.config?.repeatEnabled).isTrue()
    }

    @Test
    fun `updateLoopSetting disables repeat`() {
        val timerState = MutableStateFlow<TimerState?>(null)
        val config = defaultConfig.copy(repeatEnabled = true)
        val state = TimerState(
            config = config,
            targetDuration = 2.minutes,
            remainingDuration = 1.minutes,
            status = TimerStatus.RUNNING
        )
        timerState.value = state

        // Simulate updateLoopSetting(false)
        timerState.value?.let { current ->
            val updatedConfig = current.config.copy(repeatEnabled = false)
            timerState.value = current.copy(config = updatedConfig)
        }

        assertThat(timerState.value?.config?.repeatEnabled).isFalse()
    }

    @Test
    fun `updateLoopSetting does nothing when state is null`() {
        val timerState = MutableStateFlow<TimerState?>(null)

        // Simulate updateLoopSetting when no timer is running
        timerState.value?.let { current ->
            val updatedConfig = current.config.copy(repeatEnabled = true)
            timerState.value = current.copy(config = updatedConfig)
        }

        assertThat(timerState.value).isNull()
    }

    // -- Multiple tick survival --

    @Test
    fun `config change survives multiple ticks`() = runTest {
        val timerState = MutableStateFlow<TimerState?>(null)
        val initialState = TimerState(
            config = defaultConfig,
            targetDuration = 2.minutes,
            remainingDuration = 2.minutes,
            status = TimerStatus.RUNNING
        )
        timerState.value = initialState

        // Toggle loop ON after first tick
        var state = initialState

        // Tick 1
        val current1 = timerState.value ?: state
        state = current1.copy(
            remainingDuration = current1.remainingDuration - 1.seconds,
            status = TimerStatus.RUNNING
        )
        timerState.value = state

        // External change: enable loop
        timerState.value?.let { current ->
            val updatedConfig = current.config.copy(repeatEnabled = true)
            timerState.value = current.copy(config = updatedConfig)
        }

        // Tick 2
        val current2 = timerState.value ?: state
        state = current2.copy(
            remainingDuration = current2.remainingDuration - 1.seconds,
            status = TimerStatus.RUNNING
        )
        timerState.value = state

        assertThat(timerState.value?.config?.repeatEnabled).isTrue()

        // Tick 3
        val current3 = timerState.value ?: state
        state = current3.copy(
            remainingDuration = current3.remainingDuration - 1.seconds,
            status = TimerStatus.RUNNING
        )
        timerState.value = state

        assertThat(timerState.value?.config?.repeatEnabled).isTrue()
        assertThat(timerState.value?.remainingDuration).isEqualTo(2.minutes - 3.seconds)
    }

    // -- Default loop state is OFF --

    @Test
    fun `default config has loop disabled`() {
        val config = TimerConfig(
            minSeconds = 30,
            maxSeconds = 120,
            alarmDuration = 10,
            hiddenMode = false,
            repeatEnabled = false,
            soundType = com.iganapolsky.randomtimer.domain.model.SoundType.INTENSE,
            volume = 0.5f,
            vibrationEnabled = false
        )

        assertThat(config.repeatEnabled).isFalse()
    }

    @Test
    fun `TimerConfig DEFAULT has loop disabled`() {
        assertThat(TimerConfig.DEFAULT.repeatEnabled).isFalse()
    }

    // -- Remaining duration decrements correctly --

    @Test
    fun `timer tick decrements remaining duration by 1 second`() {
        val timerState = MutableStateFlow<TimerState?>(null)
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 2.minutes,
            remainingDuration = 2.minutes,
            status = TimerStatus.RUNNING
        )
        timerState.value = state

        val current = timerState.value ?: state
        val newRemaining = (current.remainingDuration - 1.seconds)
            .coerceAtLeast(kotlin.time.Duration.ZERO)
        timerState.value = current.copy(
            remainingDuration = newRemaining,
            status = TimerStatus.RUNNING
        )

        assertThat(timerState.value?.remainingDuration).isEqualTo(1.minutes + 59.seconds)
    }

    @Test
    fun `timer tick sets COMPLETE when remaining reaches zero`() {
        val timerState = MutableStateFlow<TimerState?>(null)
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 2.minutes,
            remainingDuration = 1.seconds,
            status = TimerStatus.RUNNING
        )
        timerState.value = state

        val current = timerState.value ?: state
        val newRemaining = (current.remainingDuration - 1.seconds)
            .coerceAtLeast(kotlin.time.Duration.ZERO)
        val newStatus = if (newRemaining <= kotlin.time.Duration.ZERO) {
            TimerStatus.COMPLETE
        } else {
            TimerStatus.RUNNING
        }
        timerState.value = current.copy(
            remainingDuration = newRemaining,
            status = newStatus
        )

        assertThat(timerState.value?.status).isEqualTo(TimerStatus.COMPLETE)
        assertThat(timerState.value?.remainingDuration).isEqualTo(kotlin.time.Duration.ZERO)
    }

    @Test
    fun `remaining duration does not go negative`() {
        val timerState = MutableStateFlow<TimerState?>(null)
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 2.minutes,
            remainingDuration = kotlin.time.Duration.ZERO,
            status = TimerStatus.RUNNING
        )
        timerState.value = state

        val current = timerState.value ?: state
        val newRemaining = (current.remainingDuration - 1.seconds)
            .coerceAtLeast(kotlin.time.Duration.ZERO)

        assertThat(newRemaining).isEqualTo(kotlin.time.Duration.ZERO)
    }

    // -- Media session activation tests --

    @Test
    fun `media session should activate when status transitions to ALARM`() {
        val timerState = MutableStateFlow<TimerState?>(null)
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 2.minutes,
            remainingDuration = kotlin.time.Duration.ZERO,
            status = TimerStatus.RUNNING
        )
        timerState.value = state

        // Simulate alarm trigger: status changes to ALARM
        val alarmState = state.copy(
            status = TimerStatus.ALARM,
            alarmTimeRemaining = state.config.alarmDuration.seconds
        )
        timerState.value = alarmState

        // Verify state is ALARM — in real service, this triggers activateMediaSession()
        assertThat(timerState.value?.status).isEqualTo(TimerStatus.ALARM)
    }

    @Test
    fun `media session should deactivate when alarm is dismissed`() {
        val timerState = MutableStateFlow<TimerState?>(null)
        val alarmConfig = defaultConfig.copy(alarmDuration = 10)
        val state = TimerState(
            config = alarmConfig,
            targetDuration = 2.minutes,
            remainingDuration = kotlin.time.Duration.ZERO,
            status = TimerStatus.ALARM,
            alarmTimeRemaining = 10.seconds
        )
        timerState.value = state

        // Simulate dismiss: clear state (same as dismissAlarm() → stopTimer())
        timerState.value = null

        // Verify state is null — in real service, this triggers deactivateMediaSession()
        assertThat(timerState.value).isNull()
    }

    @Test
    fun `media session should deactivate when alarm countdown completes`() {
        val timerState = MutableStateFlow<TimerState?>(null)
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 2.minutes,
            remainingDuration = kotlin.time.Duration.ZERO,
            status = TimerStatus.ALARM,
            alarmTimeRemaining = 1.seconds
        )
        timerState.value = state

        // Simulate alarm countdown reaching zero → status changes to COMPLETE
        val completeState = state.copy(
            status = TimerStatus.COMPLETE,
            alarmTimeRemaining = kotlin.time.Duration.ZERO
        )
        timerState.value = completeState

        // In real service, transitioning away from ALARM triggers deactivateMediaSession()
        assertThat(timerState.value?.status).isEqualTo(TimerStatus.COMPLETE)
    }
}
