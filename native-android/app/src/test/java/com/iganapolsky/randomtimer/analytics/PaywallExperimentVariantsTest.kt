package com.iganapolsky.randomtimer.analytics

import org.junit.Assert.assertEquals
import org.junit.Test

class PaywallExperimentVariantsTest {
    @Test
    fun `fromAnnualDefaultFlag maps to stable funnel labels`() {
        assertEquals("monthly_default", PaywallExperimentVariants.fromAnnualDefaultFlag(false))
        assertEquals("annual_default", PaywallExperimentVariants.fromAnnualDefaultFlag(true))
    }

    @Test
    fun `posthog flag key matches iOS`() {
        assertEquals("paywall_default_plan_annual", PostHogExperimentKeys.PAYWALL_DEFAULT_PLAN_ANNUAL)
    }
}
