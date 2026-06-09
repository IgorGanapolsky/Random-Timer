package com.iganapolsky.randomtimer.ui.screens

import com.iganapolsky.randomtimer.billing.ProManager
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PaywallPurchaseReadinessTest {
    @Test
    fun `purchase blocked when billing disconnected despite cached product ids`() {
        assertFalse(
            isPaywallPurchaseAllowed(
                billingCatalogProbed = true,
                billingReady = false,
                availableProductIds = setOf(ProManager.ELITE_PRODUCT_ID),
                selectedProductId = ProManager.ELITE_PRODUCT_ID,
            ),
        )
    }

    @Test
    fun `purchase allowed when billing ready and selected product is available`() {
        assertTrue(
            isPaywallPurchaseAllowed(
                billingCatalogProbed = true,
                billingReady = true,
                availableProductIds = setOf(ProManager.ELITE_PRODUCT_ID),
                selectedProductId = ProManager.ELITE_PRODUCT_ID,
            ),
        )
    }

    @Test
    fun `purchase blocked when catalog not probed`() {
        assertFalse(
            isPaywallPurchaseAllowed(
                billingCatalogProbed = false,
                billingReady = true,
                availableProductIds = setOf(ProManager.ELITE_PRODUCT_ID),
                selectedProductId = ProManager.ELITE_PRODUCT_ID,
            ),
        )
    }

    @Test
    fun `purchase blocked when selected product missing from refreshed catalog`() {
        assertFalse(
            isPaywallPurchaseAllowed(
                billingCatalogProbed = true,
                billingReady = true,
                availableProductIds = setOf(ProManager.BASE_PRODUCT_ID),
                selectedProductId = ProManager.ELITE_PRODUCT_ID,
            ),
        )
    }
}
