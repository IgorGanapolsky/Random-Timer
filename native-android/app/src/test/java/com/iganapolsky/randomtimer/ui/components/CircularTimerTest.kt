package com.iganapolsky.randomtimer.ui.components

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import org.junit.Test
import kotlin.time.Duration
import kotlin.time.Duration.Companion.hours
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

class CircularTimerTest {
    // -- Animation timing parity tests (must match iOS CircularTimerView) --

    @Test
    fun `circle pulse full cycle is 3 seconds`() {
        // tween(1500ms, Reverse) = 1500ms up + 1500ms down = 3000ms
        assertThat(CircularTimerAnimationConfig.CIRCLE_PULSE_ONE_WAY_MS).isEqualTo(1500)
        assertThat(CircularTimerAnimationConfig.CIRCLE_PULSE_FULL_CYCLE_MS).isEqualTo(3000)
    }

    @Test
    fun `circle pulse alpha range is 0_3 to 0_7`() {
        assertThat(CircularTimerAnimationConfig.CIRCLE_PULSE_ALPHA_MIN).isEqualTo(0.3f)
        assertThat(CircularTimerAnimationConfig.CIRCLE_PULSE_ALPHA_MAX).isEqualTo(0.7f)
    }

    @Test
    fun `text breathing full cycle is 4 seconds`() {
        // tween(2000ms, Reverse) = 2000ms up + 2000ms down = 4000ms
        assertThat(CircularTimerAnimationConfig.TEXT_BREATHING_ONE_WAY_MS).isEqualTo(2000)
        assertThat(CircularTimerAnimationConfig.TEXT_BREATHING_FULL_CYCLE_MS).isEqualTo(4000)
    }

    @Test
    fun `text breathing opacity range is 1_0 to 0_85`() {
        assertThat(CircularTimerAnimationConfig.TEXT_BREATHING_OPACITY_MAX).isEqualTo(1.0f)
        assertThat(CircularTimerAnimationConfig.TEXT_BREATHING_OPACITY_MIN).isEqualTo(0.85f)
    }

    @Test
    fun `paused status does not breathe text`() {
        assertThat(shouldBreatheText(TimerStatus.PAUSED)).isFalse()
    }

    @Test
    fun `running status breathes text`() {
        assertThat(shouldBreatheText(TimerStatus.RUNNING)).isTrue()
    }

    @Test
    fun `paused status uses higher track alpha for readability`() {
        assertThat(effectiveTrackAlpha(TimerStatus.PAUSED, 0.3f)).isEqualTo(0.45f)
    }

    // -- formatDuration tests --

    @Test
    fun `formatDuration formats minutes and seconds`() {
        val duration = 2.minutes + 30.seconds

        val result = formatDuration(duration)

        assertThat(result).isEqualTo("02:30")
    }

    @Test
    fun `formatDuration pads single digit minutes`() {
        val duration = 5.minutes + 5.seconds

        val result = formatDuration(duration)

        assertThat(result).isEqualTo("05:05")
    }

    @Test
    fun `formatDuration handles zero`() {
        val result = formatDuration(Duration.ZERO)

        assertThat(result).isEqualTo("00:00")
    }

    @Test
    fun `formatDuration handles over 60 minutes`() {
        val duration = 90.minutes + 15.seconds

        val result = formatDuration(duration)

        assertThat(result).isEqualTo("90:15")
    }

    @Test
    fun `formatDuration handles negative duration as zero`() {
        val duration = (-5).seconds

        val result = formatDuration(duration)

        assertThat(result).isEqualTo("00:00")
    }

    @Test
    fun `formatDuration handles 59 seconds`() {
        val duration = 59.seconds

        val result = formatDuration(duration)

        assertThat(result).isEqualTo("00:59")
    }

    @Test
    fun `formatDuration handles exactly 1 hour`() {
        val duration = 1.hours

        val result = formatDuration(duration)

        assertThat(result).isEqualTo("60:00")
    }
}
