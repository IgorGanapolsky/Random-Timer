package com.iganapolsky.randomtimer.domain.model

import com.google.common.truth.Truth.assertThat
import org.junit.Test
import kotlin.time.Duration
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

class TimerStateTest {
    private val defaultConfig = TimerConfig.DEFAULT

    @Test
    fun `progress is 0 at start`() {
        val state =
            TimerState(
                config = defaultConfig,
                targetDuration = 5.minutes,
                remainingDuration = 5.minutes,
                status = TimerStatus.RUNNING,
            )

        assertThat(state.progress).isEqualTo(0f)
    }

    @Test
    fun `progress uses maxSeconds not targetDuration`() {
        // Config maxSeconds=120 (2min). Target=2min, elapsed=1min.
        // progress = elapsed/max = 60/120 = 0.5
        val state =
            TimerState(
                config = defaultConfig, // maxSeconds = 120
                targetDuration = 2.minutes,
                remainingDuration = 1.minutes,
                status = TimerStatus.RUNNING,
            )

        assertThat(state.progress).isWithin(0.001f).of(0.5f)
    }

    @Test
    fun `progress caps at 0_98 never reaches 1`() {
        // Even when target equals maxSeconds and remaining is 0,
        // progress should cap at 0.98 (matching iOS unpredictableProgress)
        val state =
            TimerState(
                config = defaultConfig, // maxSeconds = 300
                targetDuration = 5.minutes,
                remainingDuration = Duration.ZERO,
                status = TimerStatus.COMPLETE,
            )

        assertThat(state.progress).isEqualTo(0.98f)
    }

    @Test
    fun `progress for short target within large max range`() {
        // Config maxSeconds=120. Target=30s, elapsed=15s.
        // progress = 15/120 = 0.125
        val state =
            TimerState(
                config = defaultConfig,
                targetDuration = 30.seconds,
                remainingDuration = 15.seconds,
                status = TimerStatus.RUNNING,
            )

        assertThat(state.progress).isWithin(0.001f).of(0.125f)
    }

    @Test
    fun `isComplete true when status is COMPLETE`() {
        val state =
            TimerState(
                config = defaultConfig,
                targetDuration = 5.minutes,
                remainingDuration = Duration.ZERO,
                status = TimerStatus.COMPLETE,
            )

        assertThat(state.isComplete).isTrue()
    }

    @Test
    fun `isComplete false when remaining is zero but status is RUNNING`() {
        // isComplete is based on status, not remaining duration
        val state =
            TimerState(
                config = defaultConfig,
                targetDuration = 5.minutes,
                remainingDuration = Duration.ZERO,
                status = TimerStatus.RUNNING,
            )

        assertThat(state.isComplete).isFalse()
    }

    @Test
    fun `isComplete true when status is ALARM`() {
        val state =
            TimerState(
                config = defaultConfig,
                targetDuration = 5.minutes,
                remainingDuration = Duration.ZERO,
                status = TimerStatus.ALARM,
            )

        assertThat(state.isComplete).isFalse() // ALARM is not COMPLETE
    }

    @Test
    fun `isComplete false when still running`() {
        val state =
            TimerState(
                config = defaultConfig,
                targetDuration = 5.minutes,
                remainingDuration = 2.minutes,
                status = TimerStatus.RUNNING,
            )

        assertThat(state.isComplete).isFalse()
    }

    @Test
    fun `shouldShowAlarmNotification true when alarm active and not silenced`() {
        val state =
            TimerState(
                config = defaultConfig,
                targetDuration = 5.minutes,
                remainingDuration = Duration.ZERO,
                status = TimerStatus.ALARM,
                alarmTimeRemaining = 10.seconds,
                isAlarmSilenced = false,
            )

        assertThat(state.shouldShowAlarmNotification).isTrue()
    }

    @Test
    fun `shouldShowAlarmNotification false when alarm is silenced`() {
        val state =
            TimerState(
                config = defaultConfig,
                targetDuration = 5.minutes,
                remainingDuration = Duration.ZERO,
                status = TimerStatus.ALARM,
                alarmTimeRemaining = 8.seconds,
                isAlarmSilenced = true,
            )

        assertThat(state.shouldShowAlarmNotification).isFalse()
    }

    @Test
    fun `shouldShowAlarmNotification false when status is not ALARM`() {
        val state =
            TimerState(
                config = defaultConfig,
                targetDuration = 5.minutes,
                remainingDuration = 2.minutes,
                status = TimerStatus.RUNNING,
            )

        assertThat(state.shouldShowAlarmNotification).isFalse()
    }

    @Test
    fun `progress handles zero max duration`() {
        val zeroConfig = defaultConfig.copy(minSeconds = 0, maxSeconds = 0)
        val state =
            TimerState(
                config = zeroConfig,
                targetDuration = Duration.ZERO,
                remainingDuration = Duration.ZERO,
                status = TimerStatus.COMPLETE,
            )

        // Should not crash, return 0
        assertThat(state.progress).isEqualTo(0f)
    }
}
