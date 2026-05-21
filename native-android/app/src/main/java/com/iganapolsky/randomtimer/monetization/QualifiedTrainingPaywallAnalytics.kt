package com.iganapolsky.randomtimer.monetization

import com.iganapolsky.randomtimer.analytics.AnalyticsProperties

object QualifiedTrainingPaywallAnalytics {
    fun eligibleProperties(completedSessionCount: Int): Map<String, Any> =
        mapOf(
            AnalyticsProperties.ENTRY_POINT to QualifiedTrainingPaywallPolicy.ENTRY_POINT,
            "completed_session_count" to completedSessionCount,
            "monetization_phase" to "p0_qualified_training_gate",
        )
}
