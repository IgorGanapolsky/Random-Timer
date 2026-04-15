package com.iganapolsky.randomtimer.analytics

/** PostHog feature-flag keys shared with iOS (`PostHogExperimentKeys`). */
object PostHogExperimentKeys {
    const val PAYWALL_DEFAULT_PLAN_ANNUAL = "paywall_default_plan_annual"
    /** Multivariate / string flag: `control` vs `outcomes_first` (paywall copy experiment). */
    const val PAYWALL_VALUE_FRAMING = "paywall_value_framing"
}

/** Values for [PostHogExperimentKeys.PAYWALL_VALUE_FRAMING] (must match iOS). */
object PaywallValueFraming {
    const val CONTROL = "control"
    const val OUTCOMES_FIRST = "outcomes_first"
}

object PaywallExperimentVariants {
    const val MONTHLY_DEFAULT = "monthly_default"
    const val ANNUAL_DEFAULT = "annual_default"

    fun fromAnnualDefaultFlag(enabled: Boolean): String = if (enabled) ANNUAL_DEFAULT else MONTHLY_DEFAULT
}
