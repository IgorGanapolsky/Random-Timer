package com.iganapolsky.randomtimer.review

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class StoreReviewManagerGateTest {
    @Test
    fun `review milestone advances from 3 to 10 to 25 then every 25 completions`() {
        assertThat(reviewPromptMilestoneForCompletionCount(2)).isNull()
        assertThat(reviewPromptMilestoneForCompletionCount(3)).isEqualTo(3)
        assertThat(reviewPromptMilestoneForCompletionCount(9)).isEqualTo(3)
        assertThat(reviewPromptMilestoneForCompletionCount(10)).isEqualTo(10)
        assertThat(reviewPromptMilestoneForCompletionCount(24)).isEqualTo(10)
        assertThat(reviewPromptMilestoneForCompletionCount(25)).isEqualTo(25)
        assertThat(reviewPromptMilestoneForCompletionCount(74)).isEqualTo(50)
    }

    @Test
    fun `review prompt requires a new milestone`() {
        val eligible =
            isEligibleForReviewPrompt(
                completionCount = 4,
                lastPromptMilestone = 3,
                lastReviewTimestampMillis = 0L,
                nowMillis = 86_400_000L,
                minDaysBetweenRequests = 30L,
            )

        assertThat(eligible).isFalse()
    }

    @Test
    fun `review prompt respects cooldown even after a new milestone`() {
        val now = 40L * 86_400_000L
        val eligible =
            isEligibleForReviewPrompt(
                completionCount = 10,
                lastPromptMilestone = 3,
                lastReviewTimestampMillis = now - (10L * 86_400_000L),
                nowMillis = now,
                minDaysBetweenRequests = 30L,
            )

        assertThat(eligible).isFalse()
    }

    @Test
    fun `review prompt becomes eligible after cooldown and new milestone`() {
        val now = 40L * 86_400_000L
        val eligible =
            isEligibleForReviewPrompt(
                completionCount = 10,
                lastPromptMilestone = 3,
                lastReviewTimestampMillis = now - (31L * 86_400_000L),
                nowMillis = now,
                minDaysBetweenRequests = 30L,
            )

        assertThat(eligible).isTrue()
    }
}
