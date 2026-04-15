package com.iganapolsky.randomtimer.analytics

/** PostHog feature-flag keys shared with iOS (`PostHogExperimentKeys`). */
object PostHogExperimentKeys {
    const val PAYWALL_DEFAULT_PLAN_ANNUAL = "paywall_default_plan_annual"
}

object PaywallExperimentVariants {
    const val MONTHLY_DEFAULT = "monthly_default"
    const val ANNUAL_DEFAULT = "annual_default"

    fun fromAnnualDefaultFlag(enabled: Boolean): String = if (enabled) ANNUAL_DEFAULT else MONTHLY_DEFAULT
}
