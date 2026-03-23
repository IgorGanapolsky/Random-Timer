package com.iganapolsky.randomtimer.ui.screens

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class ActiveTimerScreenBadgeTextTest {
    @Test
    fun loopBadgeShowsOffStateWhenDisabled() {
        assertThat(loopBadgeText(enabled = false, repeatRounds = 4, roundCount = 2)).isEqualTo("Loop Off")
    }

    @Test
    fun loopBadgeShowsInfiniteLabelWhenEnabledWithoutRoundCap() {
        assertThat(loopBadgeText(enabled = true, repeatRounds = 0, roundCount = 3)).isEqualTo("Infinite Loop")
    }

    @Test
    fun loopBadgeShowsFiniteRoundProgressWhenRoundCapIsSet() {
        assertThat(loopBadgeText(enabled = true, repeatRounds = 5, roundCount = 2)).isEqualTo("Loop On · Round 2/5")
    }

    @Test
    fun loopBadgeClampsVisibleRoundToConfiguredLimit() {
        assertThat(loopBadgeText(enabled = true, repeatRounds = 3, roundCount = 7)).isEqualTo("Loop On · Round 3/3")
    }
}
