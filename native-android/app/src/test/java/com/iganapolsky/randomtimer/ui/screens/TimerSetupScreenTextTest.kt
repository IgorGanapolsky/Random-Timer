package com.iganapolsky.randomtimer.ui.screens

import android.content.Context
import android.content.SharedPreferences
import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import io.mockk.every
import io.mockk.mockk
import org.junit.Test

class TimerSetupScreenTextTest {
    @Test
    fun repeatLoopDetailTitleShowsRoundSelectionForPro() {
        assertThat(repeatLoopDetailTitle(isPro = true)).isEqualTo("Round Selection")
    }

    @Test
    fun repeatLoopDetailTitleShowsLoopModeForFreeTier() {
        assertThat(repeatLoopDetailTitle(isPro = false)).isEqualTo("Round Selection")
    }

    @Test
    fun repeatLoopDetailSummaryShowsInfiniteRoundsForProWithoutCap() {
        assertThat(repeatLoopDetailSummary(isPro = true, repeatRounds = 0)).isEqualTo("Infinite Rounds")
    }

    @Test
    fun repeatLoopDetailSummaryExplainsFreeTierLockClearly() {
        assertThat(repeatLoopDetailSummary(isPro = false, repeatRounds = 0))
            .isEqualTo("Infinite Loop (Pro: set 1–100 rounds)")
    }

    @Test
    fun startButtonUsesFirstSessionCopyBeforeFirstCompletion() {
        assertThat(primaryStartButtonText(hasFirstCompleted = false)).isEqualTo("Start First Drill")
        assertThat(primaryStartButtonCaption(hasFirstCompleted = false))
            .isEqualTo("Quick start: the default drill fires in 5-30 seconds.")
    }

    @Test
    fun startButtonUsesGenericCopyAfterFirstCompletion() {
        assertThat(primaryStartButtonText(hasFirstCompleted = true)).isEqualTo("Start Timer")
        assertThat(primaryStartButtonCaption(hasFirstCompleted = true)).isNull()
    }

    @Test
    fun readsFirstCompletionFlagFromAnalyticsPreferences() {
        val context = mockk<Context>()
        val prefs = mockk<SharedPreferences>()
        every {
            context.getSharedPreferences(AnalyticsService.PREFS_NAME, Context.MODE_PRIVATE)
        } returns prefs
        every {
            prefs.getBoolean(AnalyticsService.KEY_HAS_COMPLETED, false)
        } returns true

        assertThat(readHasFirstCompleted(context)).isTrue()
    }

    @Test
    fun competitionPrepSectionTitleMatchesIOS() {
        assertThat(competitionPrepSectionTitle()).isEqualTo("Competition Prep")
    }

    @Test
    fun competitionPrepIsAvailableWithoutPro() {
        assertThat(isCompetitionPrepProGated()).isFalse()
    }
}
