package com.iganapolsky.randomtimer.ui.screens

import com.iganapolsky.randomtimer.billing.ProManager
import org.junit.Assert.assertEquals
import org.junit.Test

class PaywallSheetTest {
    @Test
    fun `hidden unlock hold duration is eight seconds`() {
        assertEquals(8_000L, HIDDEN_UNLOCK_HOLD_DURATION_MS)
    }

    @Test
    fun `paywall copy focuses on training outcomes`() {
        assertEquals("Stop Training With the Brakes On", PAYWALL_HEADLINE)
        assertEquals(
            "Go unlimited — sessions up to 60 minutes, live voice callouts, and a full sound library that updates every month.",
            PAYWALL_SUBHEADLINE,
        )
        assertEquals("Cancel anytime. Subscription auto-renews until cancelled.", PAYWALL_PRICING_FOOTER)
        assertEquals(
            listOf(
                "Full-length sessions — up to 60 minutes, no cutoffs",
                "Live voice callouts keep you sharp under pressure",
                "Loop drills with round limits — just like competition",
                "Full sound arsenal — real bells, horns, and sirens",
                "Fresh callout packs every 30 days — Pro gets them first",
            ),
            PAYWALL_FEATURE_ROWS,
        )
    }

    @Test
    fun `price label normalizes to yearly pricing`() {
        assertEquals("$29.99/year", normalizedPriceLabel("$29.99"))
        assertEquals("$29.99/yr", normalizedPriceLabel("$29.99/yr"))
    }

    @Test
    fun `stripPriceSuffix removes trailing slash unit`() {
        assertEquals("$3.99", stripPriceSuffix("$3.99/mo"))
        assertEquals("$3.99", stripPriceSuffix("$3.99/month"))
        assertEquals("$29.99", stripPriceSuffix("$29.99/yr"))
        assertEquals("$29.99", stripPriceSuffix("$29.99/year"))
        assertEquals("$29.99", stripPriceSuffix("$29.99"))
    }

    @Test
    fun `subscription plan selection enum has monthly and annual variants`() {
        val monthly = SubscriptionPlanSelection.MONTHLY
        val annual = SubscriptionPlanSelection.ANNUAL
        assertEquals(SubscriptionPlanSelection.MONTHLY, monthly)
        assertEquals(SubscriptionPlanSelection.ANNUAL, annual)
    }

    @Test
    fun `cta label uses trial eligibility for the selected product only`() {
        val trialEligibility =
            mapOf(
                ProManager.MONTHLY_PRODUCT_ID to false,
                ProManager.ELITE_PRODUCT_ID to true,
            )

        assertEquals(
            "Start Monthly \u2022 $3.99/mo",
            ctaLabelForPlan(
                selectedPlan = SubscriptionPlanSelection.MONTHLY,
                proPrice = "$29.99",
                monthlyPrice = "$3.99",
                trialEligibilityByProductId = trialEligibility,
            ),
        )
        assertEquals(
            "Start 7-Day Free Trial",
            ctaLabelForPlan(
                selectedPlan = SubscriptionPlanSelection.ANNUAL,
                proPrice = "$29.99",
                monthlyPrice = "$3.99",
                trialEligibilityByProductId = trialEligibility,
            ),
        )
    }
}
