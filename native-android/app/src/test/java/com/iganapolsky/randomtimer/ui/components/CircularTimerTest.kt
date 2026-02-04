package com.iganapolsky.randomtimer.ui.components

import com.google.common.truth.Truth.assertThat
import org.junit.Test
import kotlin.time.Duration
import kotlin.time.Duration.Companion.hours
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

class CircularTimerTest {

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
