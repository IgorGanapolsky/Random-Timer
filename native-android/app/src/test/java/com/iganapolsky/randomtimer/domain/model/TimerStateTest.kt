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
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 5.minutes,
            remainingDuration = 5.minutes,
            status = TimerStatus.RUNNING
        )

        assertThat(state.progress).isEqualTo(0f)
    }

    @Test
    fun `progress is 0_5 at halfway`() {
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 10.minutes,
            remainingDuration = 5.minutes,
            status = TimerStatus.RUNNING
        )

        assertThat(state.progress).isWithin(0.001f).of(0.5f)
    }

    @Test
    fun `progress is 1 when complete`() {
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 5.minutes,
            remainingDuration = Duration.ZERO,
            status = TimerStatus.COMPLETE
        )

        assertThat(state.progress).isEqualTo(1f)
    }

    @Test
    fun `isComplete true when status is COMPLETE`() {
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 5.minutes,
            remainingDuration = Duration.ZERO,
            status = TimerStatus.COMPLETE
        )

        assertThat(state.isComplete).isTrue()
    }

    @Test
    fun `isComplete false when remaining is zero but status is RUNNING`() {
        // isComplete is based on status, not remaining duration
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 5.minutes,
            remainingDuration = Duration.ZERO,
            status = TimerStatus.RUNNING
        )

        assertThat(state.isComplete).isFalse()
    }

    @Test
    fun `isComplete true when status is ALARM`() {
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 5.minutes,
            remainingDuration = Duration.ZERO,
            status = TimerStatus.ALARM
        )

        assertThat(state.isComplete).isFalse() // ALARM is not COMPLETE
    }

    @Test
    fun `isComplete false when still running`() {
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 5.minutes,
            remainingDuration = 2.minutes,
            status = TimerStatus.RUNNING
        )

        assertThat(state.isComplete).isFalse()
    }

    @Test
    fun `shouldShowAlarmNotification true when alarm active and not silenced`() {
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 5.minutes,
            remainingDuration = Duration.ZERO,
            status = TimerStatus.ALARM,
            alarmTimeRemaining = 10.seconds,
            isAlarmSilenced = false
        )

        assertThat(state.shouldShowAlarmNotification).isTrue()
    }

    @Test
    fun `shouldShowAlarmNotification false when alarm is silenced`() {
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 5.minutes,
            remainingDuration = Duration.ZERO,
            status = TimerStatus.ALARM,
            alarmTimeRemaining = 8.seconds,
            isAlarmSilenced = true
        )

        assertThat(state.shouldShowAlarmNotification).isFalse()
    }

    @Test
    fun `shouldShowAlarmNotification false when status is not ALARM`() {
        val state = TimerState(
            config = defaultConfig,
            targetDuration = 5.minutes,
            remainingDuration = 2.minutes,
            status = TimerStatus.RUNNING
        )

        assertThat(state.shouldShowAlarmNotification).isFalse()
    }

    @Test
    fun `progress handles zero target duration`() {
        val state = TimerState(
            config = defaultConfig,
            targetDuration = Duration.ZERO,
            remainingDuration = Duration.ZERO,
            status = TimerStatus.COMPLETE
        )

        // Should not crash, return 0
        assertThat(state.progress).isEqualTo(0f)
    }
}
