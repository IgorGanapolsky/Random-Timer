package com.iganapolsky.randomtimer.ui.screens

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class ActiveTimerScreenBadgeTextTest {
    @Test
    fun `loop badge shows off state when disabled`() {
        assertThat(loopBadgeText(enabled = false, repeatRounds = 4, roundCount = 2)).isEqualTo("LOOP OFF")
    }

    @Test
    fun `loop badge shows infinite label when enabled without round cap`() {
        assertThat(loopBadgeText(enabled = true, repeatRounds = 0, roundCount = 3)).isEqualTo("LOOP")
    }

    @Test
    fun `loop badge shows finite round progress when round cap is set`() {
        assertThat(loopBadgeText(enabled = true, repeatRounds = 5, roundCount = 2)).isEqualTo("ROUND 2/5")
    }

    @Test
    fun `loop badge clamps visible round to configured limit`() {
        assertThat(loopBadgeText(enabled = true, repeatRounds = 3, roundCount = 7)).isEqualTo("ROUND 3/3")
    }
}
