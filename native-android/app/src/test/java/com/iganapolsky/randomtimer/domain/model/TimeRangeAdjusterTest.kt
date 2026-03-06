package com.iganapolsky.randomtimer.domain.model

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class TimeRangeAdjusterTest {
    @Test
    fun `min change within gap keeps max unchanged`() {
        val (min, max) =
            TimeRangeAdjuster.adjustForMinChange(
                currentMinSeconds = 0,
                currentMaxSeconds = 300,
                newMinSeconds = 120,
            )

        assertThat(min).isEqualTo(120)
        assertThat(max).isEqualTo(300)
    }

    @Test
    fun `min change beyond max minus gap pushes max forward`() {
        val (min, max) =
            TimeRangeAdjuster.adjustForMinChange(
                currentMinSeconds = 0,
                currentMaxSeconds = 10,
                newMinSeconds = 15,
            )

        assertThat(min).isEqualTo(15)
        assertThat(max).isEqualTo(15)
    }

    @Test
    fun `reported bug zero to thirty range is possible`() {
        // User sets min to 0
        val (min1, max1) =
            TimeRangeAdjuster.adjustForMinChange(
                currentMinSeconds = 10,
                currentMaxSeconds = 30,
                newMinSeconds = 0,
            )
        assertThat(min1).isEqualTo(0)
        assertThat(max1).isEqualTo(30)

        // User sets max to 30
        val (min2, max2) =
            TimeRangeAdjuster.adjustForMaxChange(
                currentMinSeconds = 0,
                currentMaxSeconds = 30,
                newMaxSeconds = 30,
            )
        assertThat(min2).isEqualTo(0)
        assertThat(max2).isEqualTo(30)
    }

    @Test
    fun `min change that would exceed max limit clamps to max minus gap`() {
        val cap = 300
        val (min, max) =
            TimeRangeAdjuster.adjustForMinChange(
                currentMinSeconds = 250,
                currentMaxSeconds = 300,
                newMinSeconds = 305,
                maxSecondsLimit = cap,
            )

        assertThat(min).isEqualTo(cap)
        assertThat(max).isEqualTo(cap)
    }

    @Test
    fun `max change within gap keeps min unchanged`() {
        val (min, max) =
            TimeRangeAdjuster.adjustForMaxChange(
                currentMinSeconds = 0,
                currentMaxSeconds = 300,
                newMaxSeconds = 200,
            )

        assertThat(min).isEqualTo(0)
        assertThat(max).isEqualTo(200)
    }

    @Test
    fun `max change below min plus gap pulls min back`() {
        val (min, max) =
            TimeRangeAdjuster.adjustForMaxChange(
                currentMinSeconds = 100,
                currentMaxSeconds = 200,
                newMaxSeconds = 50,
            )

        assertThat(min).isEqualTo(50)
        assertThat(max).isEqualTo(50)
    }

    @Test
    fun `max change that would pull min below limit clamps to min limit`() {
        val (min, max) =
            TimeRangeAdjuster.adjustForMaxChange(
                currentMinSeconds = 10,
                currentMaxSeconds = 40,
                newMaxSeconds = 0,
            )

        assertThat(min).isEqualTo(0)
        assertThat(max).isEqualTo(0)
    }

    @Test
    fun `min change with custom cap keeps gap and stays within cap`() {
        val cap = TimerConfig.MAX_SECONDS_PRO
        val (min, max) =
            TimeRangeAdjuster.adjustForMinChange(
                currentMinSeconds = 3400,
                currentMaxSeconds = 3550,
                newMinSeconds = cap,
                maxSecondsLimit = cap,
            )

        assertThat(max).isEqualTo(cap)
        assertThat(min).isEqualTo(cap)
    }

    @Test
    fun `max change above free cap clamps and keeps valid window`() {
        val cap = TimerConfig.MAX_SECONDS_FREE
        val (min, max) =
            TimeRangeAdjuster.adjustForMaxChange(
                currentMinSeconds = cap, // Min is already at the cap
                currentMaxSeconds = cap,
                newMaxSeconds = cap + 120,
                maxSecondsLimit = cap,
            )

        assertThat(max).isEqualTo(cap)
        assertThat(min).isEqualTo(cap)
    }
}
