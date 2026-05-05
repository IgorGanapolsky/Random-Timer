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
        assertEquals("Unlock Full Fight-Ready Training", PAYWALL_HEADLINE)
        assertEquals(
            "Unlock 60-minute random windows, combat voice callouts, round-capped loops, and the full sound arsenal built for pressure drills.",
            PAYWALL_SUBHEADLINE,
        )
        assertEquals("Cancel anytime. Subscription auto-renews until cancelled.", PAYWALL_PRICING_FOOTER)
        assertEquals(
            listOf(
                "60-minute random windows for full-length drills",
                "Combat and MMA voice callouts with live time checks",
                "Round-capped loops for pad work, sparring, and circuits",
                "Full sound arsenal — bells, horns, sirens, and more",
                "Fresh pro audio drops when new packs land",
            ),
            PAYWALL_FEATURE_ROWS,
        )
    }

    @Test
    fun `paywall feature context explains selected gate value`() {
        val setupContext = paywallFeatureContext("setup_upgrade_cta")
        assertEquals("You tapped Unlock Pro", setupContext.eyebrow)

        val rangeContext = paywallFeatureContext("range_gate")
        assertEquals("You tapped 60-minute random windows", rangeContext.eyebrow)
        assertEquals(
            "Pro removes the 5-minute cap so long rounds, circuits, and stress drills can run on your timing.",
            rangeContext.valueCopy,
        )

        val unknownContext = paywallFeatureContext("unknown")
        assertEquals("Pro Tactical", unknownContext.eyebrow)
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
        assertEquals("monthly", planNameForSelection(monthly))
        assertEquals("annual", planNameForSelection(annual))
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
