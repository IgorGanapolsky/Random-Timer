package com.iganapolsky.randomtimer.monetization

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsProperties
import org.junit.Test

class QualifiedTrainingPaywallAnalyticsTest {
    @Test
    fun `eligible event name matches iOS contract`() {
        assertThat(AnalyticsEvents.QUALIFIED_TRAINING_PAYWALL_ELIGIBLE)
            .isEqualTo("qualified_training_paywall_eligible")
    }

    @Test
    fun `eligibleProperties carries session count and entry point`() {
        val properties =
            QualifiedTrainingPaywallAnalytics.eligibleProperties(
                completedSessionCount = 3,
            )

        assertThat(properties[AnalyticsProperties.ENTRY_POINT])
            .isEqualTo(QualifiedTrainingPaywallPolicy.ENTRY_POINT)
        assertThat(properties["completed_session_count"]).isEqualTo(3)
        assertThat(properties["monetization_phase"]).isEqualTo("p0_qualified_training_gate")
    }
}
