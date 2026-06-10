package com.iganapolsky.randomtimer.ui.screens

import com.iganapolsky.randomtimer.billing.ProManager
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PaywallBillingRefreshTest {
    @Test
    fun `continues refresh while billing is not purchasable`() {
        val snapshot =
            PaywallBillingSnapshot(
                catalogProbed = true,
                billingReady = false,
                availableProductIds = emptySet(),
            )

        assertTrue(shouldContinuePaywallBillingRefresh(snapshot, attempt = 0))
    }

    @Test
    fun `stops refresh once annual plan is purchasable`() {
        val snapshot =
            PaywallBillingSnapshot(
                catalogProbed = true,
                billingReady = true,
                availableProductIds = setOf(ProManager.ELITE_PRODUCT_ID),
            )

        assertFalse(shouldContinuePaywallBillingRefresh(snapshot, attempt = 0))
    }

    @Test
    fun `stops refresh after max attempts even if billing stays unavailable`() {
        val snapshot =
            PaywallBillingSnapshot(
                catalogProbed = true,
                billingReady = false,
                availableProductIds = emptySet(),
            )

        assertFalse(
            shouldContinuePaywallBillingRefresh(
                snapshot,
                attempt = PAYWALL_BILLING_REFRESH_MAX_ATTEMPTS,
            ),
        )
    }
}
