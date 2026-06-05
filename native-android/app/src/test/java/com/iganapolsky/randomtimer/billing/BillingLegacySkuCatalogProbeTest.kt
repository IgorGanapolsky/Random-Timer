package com.iganapolsky.randomtimer.billing

import com.android.billingclient.api.BillingClient
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class BillingLegacySkuCatalogProbeTest {
    private val required =
        setOf(
            ProManager.BASE_PRODUCT_ID,
            ProManager.ELITE_PRODUCT_ID,
            ProManager.MONTHLY_PRODUCT_ID,
        )

    @Test
    fun `attempt legacy sku probe only when product details unsupported`() {
        assertThat(shouldAttemptLegacySkuCatalogProbe(productDetailsSupported = false)).isTrue()
        assertThat(shouldAttemptLegacySkuCatalogProbe(productDetailsSupported = true)).isFalse()
        assertThat(shouldAttemptLegacySkuCatalogProbe(productDetailsSupported = null)).isFalse()
    }

    @Test
    fun `legacy sku fallback returns catalog ok when required products found`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = false,
                requiredProductIds = required,
                cachedLogicalProductIds = required,
                legacySkuCatalogProbed = true,
            )

        assertThat(result.status).isEqualTo("ok")
        assertThat(result.probeBlockedReason).isNull()
        assertThat(result.availableProductIds).containsExactly(
            ProManager.BASE_PRODUCT_ID,
            ProManager.ELITE_PRODUCT_ID,
            ProManager.MONTHLY_PRODUCT_ID,
        )
    }

    @Test
    fun `legacy sku fallback returns honest degraded state when probe finds nothing`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = false,
                requiredProductIds = required,
                cachedLogicalProductIds = emptySet(),
                legacySkuCatalogProbed = true,
            )

        assertThat(result.status).isEqualTo("play_store_update_required")
        assertThat(result.probeBlockedReason).isEqualTo("legacy_sku_degraded")
        assertThat(result.availableProductIds).isEmpty()
    }

    @Test
    fun `product details unsupported before legacy probe stays blocked`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = false,
                requiredProductIds = required,
                cachedLogicalProductIds = emptySet(),
                legacySkuCatalogProbed = false,
            )

        assertThat(result.status).isEqualTo("product_details_unsupported")
        assertThat(result.probeBlockedReason).isEqualTo("product_details_unsupported")
    }

    @Test
    fun `legacy sku query maps billing ids to logical ids`() {
        val specs = buildPaywallCatalogQuerySpecs()
        val foundBillingIds = listOf(ProManager.BASE_PRODUCT_ID, ProManager.ELITE_PRODUCT_ID)

        val logicalIds = logicalProductIdsResolvedFromLegacySkuQuery(specs, foundBillingIds)

        assertThat(logicalIds).containsAtLeast(
            ProManager.BASE_PRODUCT_ID,
            ProManager.ELITE_PRODUCT_ID,
            ProManager.MONTHLY_PRODUCT_ID,
        )
    }

    @Test
    fun `legacy sku probe treats FEATURE_NOT_SUPPORTED response as degraded`() {
        assertThat(
            isLegacySkuCatalogDegraded(
                billingResponseCode = BillingClient.BillingResponseCode.FEATURE_NOT_SUPPORTED,
                foundBillingProductIds = emptyList(),
            ),
        ).isTrue()
    }

    @Test
    fun `legacy sku probe ok when billing returns sku ids`() {
        assertThat(
            isLegacySkuCatalogDegraded(
                billingResponseCode = BillingClient.BillingResponseCode.OK,
                foundBillingProductIds = listOf(ProManager.ELITE_PRODUCT_ID),
            ),
        ).isFalse()
    }
}
