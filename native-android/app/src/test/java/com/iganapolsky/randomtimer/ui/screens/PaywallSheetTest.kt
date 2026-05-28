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
        assertEquals(
            "Elite plans from about $4.99–9.99/mo (store price on checkout). Cancel anytime; subscription auto-renews until cancelled.",
            PAYWALL_PRICING_FOOTER,
        )
        assertEquals(
            listOf(
                "Ad-free training — Elite subscription removes rewarded ads",
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

        val qualifiedContext = paywallFeatureContext("qualified_training_gate")
        assertEquals("Three sessions logged", qualifiedContext.eyebrow)

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
    fun `subscription plan selection enum has monthly annual and lifetime variants`() {
        val monthly = SubscriptionPlanSelection.MONTHLY
        val annual = SubscriptionPlanSelection.ANNUAL
        val lifetime = SubscriptionPlanSelection.LIFETIME
        assertEquals(SubscriptionPlanSelection.MONTHLY, monthly)
        assertEquals(SubscriptionPlanSelection.ANNUAL, annual)
        assertEquals(SubscriptionPlanSelection.LIFETIME, lifetime)
        assertEquals("monthly", planNameForSelection(monthly))
        assertEquals("annual", planNameForSelection(annual))
        assertEquals("lifetime", planNameForSelection(lifetime))
        assertEquals(ProManager.BASE_PRODUCT_ID, productIdForPlan(lifetime))
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
                lifetimePrice = "$4.99",
                trialEligibilityByProductId = trialEligibility,
            ),
        )
        assertEquals(
            "Start 7-Day Free Trial",
            ctaLabelForPlan(
                selectedPlan = SubscriptionPlanSelection.ANNUAL,
                proPrice = "$29.99",
                monthlyPrice = "$3.99",
                lifetimePrice = "$4.99",
                trialEligibilityByProductId = trialEligibility,
            ),
        )
        assertEquals(
            "Unlock Lifetime \u2022 $4.99",
            ctaLabelForPlan(
                selectedPlan = SubscriptionPlanSelection.LIFETIME,
                proPrice = "$29.99",
                monthlyPrice = "$3.99",
                lifetimePrice = "$4.99",
                trialEligibilityByProductId = trialEligibility,
            ),
        )
    }

    @Test
    fun `setup upgrade defaults to lifetime while experiments can still force annual`() {
        assertEquals(
            SubscriptionPlanSelection.LIFETIME,
            initialPlanSelection(entryPoint = "setup_upgrade_cta", defaultToAnnualPlan = false),
        )
        assertEquals(
            SubscriptionPlanSelection.ANNUAL,
            initialPlanSelection(entryPoint = "range_gate", defaultToAnnualPlan = false),
        )
        assertEquals(
            SubscriptionPlanSelection.ANNUAL,
            initialPlanSelection(entryPoint = "voice_gate", defaultToAnnualPlan = false),
        )
        assertEquals(
            SubscriptionPlanSelection.ANNUAL,
            initialPlanSelection(entryPoint = "qualified_training_gate", defaultToAnnualPlan = false),
        )
        assertEquals(
            SubscriptionPlanSelection.ANNUAL,
            initialPlanSelection(entryPoint = "setup_upgrade_cta", defaultToAnnualPlan = true),
        )
    }

    @Test
    fun `known billing catalog hides unavailable paywall plans`() {
        val availableProductIds =
            setOf(
                ProManager.BASE_PRODUCT_ID,
                ProManager.ELITE_PRODUCT_ID,
            )

        assertEquals(
            true,
            shouldShowPaywallPlan(
                SubscriptionPlanSelection.LIFETIME,
                availableProductIds,
                billingCatalogProbed = true,
            ),
        )
        assertEquals(
            true,
            shouldShowPaywallPlan(
                SubscriptionPlanSelection.ANNUAL,
                availableProductIds,
                billingCatalogProbed = true,
            ),
        )
        assertEquals(
            false,
            shouldShowPaywallPlan(
                SubscriptionPlanSelection.MONTHLY,
                availableProductIds,
                billingCatalogProbed = true,
            ),
        )
    }

    @Test
    fun `unprobed billing catalog hides paywall plans`() {
        assertEquals(
            false,
            shouldShowPaywallPlan(SubscriptionPlanSelection.LIFETIME, emptySet(), billingCatalogProbed = false),
        )
        assertEquals(
            false,
            shouldShowPaywallPlan(SubscriptionPlanSelection.ANNUAL, emptySet(), billingCatalogProbed = false),
        )
        assertEquals(
            false,
            shouldShowPaywallPlan(SubscriptionPlanSelection.MONTHLY, emptySet(), billingCatalogProbed = false),
        )
    }

    @Test
    fun `probed empty billing catalog hides paywall plans`() {
        assertEquals(
            false,
            shouldShowPaywallPlan(SubscriptionPlanSelection.MONTHLY, emptySet(), billingCatalogProbed = true),
        )
        assertEquals(false, hasPurchasablePaywallPlan(emptySet(), billingCatalogProbed = true))
    }

    @Test
    fun `initial plan selection prefers first purchasable plan when default is missing`() {
        val available =
            setOf(
                ProManager.ELITE_PRODUCT_ID,
            )
        assertEquals(
            SubscriptionPlanSelection.ANNUAL,
            initialPlanSelection(
                entryPoint = "range_gate",
                defaultToAnnualPlan = false,
                availableProductIds = available,
                billingCatalogProbed = true,
            ),
        )
    }
}
