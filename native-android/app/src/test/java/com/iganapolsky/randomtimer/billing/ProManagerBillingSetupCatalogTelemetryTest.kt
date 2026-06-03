package com.iganapolsky.randomtimer.billing

import com.android.billingclient.api.BillingClient
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class ProManagerBillingSetupCatalogTelemetryTest {
    @Test
    fun `emit catalog status when setup OK but product details unsupported`() {
        assertThat(
            ProManager.shouldTrackCatalogStatusOnBillingSetupFinished(
                billingSetupResponseCode = BillingClient.BillingResponseCode.OK,
                productDetailsFeatureSupported = false,
            ),
        ).isTrue()
    }

    @Test
    fun `do not emit catalog status on setup when product details supported`() {
        assertThat(
            ProManager.shouldTrackCatalogStatusOnBillingSetupFinished(
                billingSetupResponseCode = BillingClient.BillingResponseCode.OK,
                productDetailsFeatureSupported = true,
            ),
        ).isFalse()
    }

    @Test
    fun `do not emit catalog status when billing setup failed`() {
        assertThat(
            ProManager.shouldTrackCatalogStatusOnBillingSetupFinished(
                billingSetupResponseCode = BillingClient.BillingResponseCode.BILLING_UNAVAILABLE,
                productDetailsFeatureSupported = false,
            ),
        ).isFalse()
    }

    @Test
    fun `catalog status for unsupported uses product_details_unsupported`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = false,
                requiredProductIds =
                    setOf(
                        ProManager.BASE_PRODUCT_ID,
                        ProManager.ELITE_PRODUCT_ID,
                        ProManager.MONTHLY_PRODUCT_ID,
                    ),
                cachedLogicalProductIds = emptySet(),
            )

        assertThat(result.status).isEqualTo("product_details_unsupported")
        assertThat(result.probeBlockedReason).isEqualTo("product_details_unsupported")
    }
}
