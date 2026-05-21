package com.iganapolsky.randomtimer.monetization

import com.iganapolsky.randomtimer.analytics.AnalyticsProperties

object RewardedAdAnalytics {
    fun requestedProperties(entryPoint: String): Map<String, Any> =
        baseProperties(entryPoint)

    fun completedProperties(
        entryPoint: String,
        success: Boolean,
    ): Map<String, Any> =
        baseProperties(entryPoint) +
            mapOf(
                AnalyticsProperties.SUCCESS to success,
            )

    fun unlockProperties(entryPoint: String): Map<String, Any> =
        baseProperties(entryPoint) +
            mapOf(
                "unlock_feature" to RewardedAdPolicy.UNLOCK_FEATURE,
            )

    private fun baseProperties(entryPoint: String): Map<String, Any> =
        mapOf(
            AnalyticsProperties.ENTRY_POINT to entryPoint,
            "unlock_feature" to RewardedAdPolicy.UNLOCK_FEATURE,
            "monetization_phase" to "p1_rewarded_ads",
            "admob_blocker" to RewardedAdConfig.ADMOB_BLOCKER,
        )
}
