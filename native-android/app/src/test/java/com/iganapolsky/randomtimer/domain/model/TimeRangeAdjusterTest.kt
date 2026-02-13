package com.iganapolsky.randomtimer.domain.model

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class TimeRangeAdjusterTest {

    @Test
    fun `min change within gap keeps max unchanged`() {
        val (min, max) = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds = 0,
            currentMaxSeconds = 300,
            newMinSeconds = 120,
        )

        assertThat(min).isEqualTo(120)
        assertThat(max).isEqualTo(300)
    }

    @Test
    fun `min change beyond max minus gap pushes max forward`() {
        val (min, max) = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds = 0,
            currentMaxSeconds = 60,
            newMinSeconds = 50,
        )

        assertThat(min).isEqualTo(50)
        assertThat(max).isEqualTo(80)
        assertThat(max - min).isAtLeast(TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS)
    }

    @Test
    fun `min change that would exceed max limit clamps to max minus gap`() {
        val (min, max) = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds = 250,
            currentMaxSeconds = 300,
            newMinSeconds = 280,
        )

        assertThat(min).isEqualTo(270)
        assertThat(max).isEqualTo(300)
        assertThat(max - min).isAtLeast(TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS)
    }

    @Test
    fun `max change within gap keeps min unchanged`() {
        val (min, max) = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds = 0,
            currentMaxSeconds = 300,
            newMaxSeconds = 200,
        )

        assertThat(min).isEqualTo(0)
        assertThat(max).isEqualTo(200)
    }

    @Test
    fun `max change below min plus gap pulls min back`() {
        val (min, max) = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds = 100,
            currentMaxSeconds = 200,
            newMaxSeconds = 110,
        )

        assertThat(min).isEqualTo(80)
        assertThat(max).isEqualTo(110)
        assertThat(max - min).isAtLeast(TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS)
    }

    @Test
    fun `max change that would pull min below limit clamps to min limit`() {
        val (min, max) = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds = 10,
            currentMaxSeconds = 40,
            newMaxSeconds = 25,
        )

        assertThat(min).isEqualTo(0)
        assertThat(max).isEqualTo(30)
        assertThat(max - min).isAtLeast(TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS)
    }
}

