package com.iganapolsky.randomtimer.ui.screens

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class TimerSetupScreenTextTest {
    @Test
    fun repeatLoopDetailTitleShowsRoundSelectionForPro() {
        assertThat(repeatLoopDetailTitle(isPro = true)).isEqualTo("Round Selection")
    }

    @Test
    fun repeatLoopDetailTitleShowsLoopModeForFreeTier() {
        assertThat(repeatLoopDetailTitle(isPro = false)).isEqualTo("Loop Mode")
    }

    @Test
    fun repeatLoopDetailSummaryShowsInfiniteRoundsForProWithoutCap() {
        assertThat(repeatLoopDetailSummary(isPro = true, repeatRounds = 0)).isEqualTo("Infinite Rounds")
    }

    @Test
    fun repeatLoopDetailSummaryExplainsFreeTierLockClearly() {
        assertThat(repeatLoopDetailSummary(isPro = false, repeatRounds = 0))
            .isEqualTo("Infinite Loop - Pro unlocks round limits")
    }
}
