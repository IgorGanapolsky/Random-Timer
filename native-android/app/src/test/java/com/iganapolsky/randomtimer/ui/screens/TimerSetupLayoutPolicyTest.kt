package com.iganapolsky.randomtimer.ui.screens

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class TimerSetupLayoutPolicyTest {
    @Test
    fun `compact mode enabled below threshold`() {
        assertThat(TimerSetupLayoutPolicy.isCompactHeightViewport(720)).isTrue()
    }

    @Test
    fun `compact mode disabled at threshold`() {
        assertThat(
            TimerSetupLayoutPolicy.isCompactHeightViewport(
                TimerSetupLayoutPolicy.COMPACT_HEIGHT_THRESHOLD_DP,
            ),
        ).isFalse()
    }

    @Test
    fun `compact mode disabled for large screens`() {
        assertThat(TimerSetupLayoutPolicy.isCompactHeightViewport(900)).isFalse()
    }
}
