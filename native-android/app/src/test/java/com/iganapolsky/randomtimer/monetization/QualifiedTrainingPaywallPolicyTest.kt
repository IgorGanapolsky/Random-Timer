package com.iganapolsky.randomtimer.monetization

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class QualifiedTrainingPaywallPolicyTest {
    @Test
    fun `does not present before third completed session`() {
        assertThat(
            QualifiedTrainingPaywallPolicy.shouldPresent(
                completedSessionCount = 2,
                isPro = false,
                alreadyPresented = false,
            ),
        ).isFalse()
    }

    @Test
    fun `presents once after third completed session for free users`() {
        assertThat(
            QualifiedTrainingPaywallPolicy.shouldPresent(
                completedSessionCount = 3,
                isPro = false,
                alreadyPresented = false,
            ),
        ).isTrue()
    }

    @Test
    fun `does not present for pro users`() {
        assertThat(
            QualifiedTrainingPaywallPolicy.shouldPresent(
                completedSessionCount = 3,
                isPro = true,
                alreadyPresented = false,
            ),
        ).isFalse()
    }

    @Test
    fun `does not present after paywall already shown`() {
        assertThat(
            QualifiedTrainingPaywallPolicy.shouldPresent(
                completedSessionCount = 3,
                isPro = false,
                alreadyPresented = true,
            ),
        ).isFalse()
    }

    @Test
    fun `does not re-present on fourth session`() {
        assertThat(
            QualifiedTrainingPaywallPolicy.shouldPresent(
                completedSessionCount = 4,
                isPro = false,
                alreadyPresented = false,
            ),
        ).isFalse()
    }
}
