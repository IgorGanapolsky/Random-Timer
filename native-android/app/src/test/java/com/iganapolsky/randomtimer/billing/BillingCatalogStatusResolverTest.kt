package com.iganapolsky.randomtimer.billing

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class BillingCatalogStatusResolverTest {
    private val required =
        setOf(
            ProManager.BASE_PRODUCT_ID,
            ProManager.ELITE_PRODUCT_ID,
            ProManager.MONTHLY_PRODUCT_ID,
        )

    @Test
    fun `empty only when billing ready and product details supported`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = true,
                requiredProductIds = required,
                cachedLogicalProductIds = emptySet(),
            )

        assertThat(result.status).isEqualTo("empty")
        assertThat(result.probeBlockedReason).isNull()
    }

    @Test
    fun `billing_not_ready when client not ready`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = false,
                productDetailsSupported = true,
                requiredProductIds = required,
                cachedLogicalProductIds = emptySet(),
            )

        assertThat(result.status).isEqualTo("billing_not_ready")
        assertThat(result.probeBlockedReason).isEqualTo("billing_not_ready")
    }

    @Test
    fun `catalog_probe_pending when product details support not yet known`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = null,
                requiredProductIds = required,
                cachedLogicalProductIds = emptySet(),
            )

        assertThat(result.status).isEqualTo("catalog_probe_pending")
        assertThat(result.probeBlockedReason).isEqualTo("catalog_probe_pending")
    }

    @Test
    fun `product_details_unsupported when Play reports feature unsupported`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = false,
                requiredProductIds = required,
                cachedLogicalProductIds = emptySet(),
            )

        assertThat(result.status).isEqualTo("product_details_unsupported")
        assertThat(result.probeBlockedReason).isEqualTo("product_details_unsupported")
    }

    @Test
    fun `ok when all required logical products cached`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = true,
                requiredProductIds = required,
                cachedLogicalProductIds = required,
            )

        assertThat(result.status).isEqualTo("ok")
        assertThat(result.missingProductIds).isEmpty()
    }

    @Test
    fun `missing_required_products when partial catalog`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = true,
                requiredProductIds = required,
                cachedLogicalProductIds = setOf(ProManager.ELITE_PRODUCT_ID),
            )

        assertThat(result.status).isEqualTo("missing_required_products")
        assertThat(result.missingProductIds).contains(ProManager.BASE_PRODUCT_ID)
    }

    @Test
    fun `catalog_query_failed when all required SKUs failed with network error after retries`() {
        val networkFailures =
            mapOf(
                ProManager.BASE_PRODUCT_ID to "network_error",
                ProManager.ELITE_PRODUCT_ID to "network_error",
                ProManager.MONTHLY_PRODUCT_ID to "network_error",
            )
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = true,
                requiredProductIds = required,
                cachedLogicalProductIds = emptySet(),
                productQueryFailureReasons = networkFailures,
            )

        assertThat(result.status).isEqualTo("catalog_query_failed")
        assertThat(result.probeBlockedReason).isEqualTo("network_error")
    }

    @Test
    fun `empty when cache empty and Play returned no SKUs without network failure`() {
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = true,
                requiredProductIds = required,
                cachedLogicalProductIds = emptySet(),
                productQueryFailureReasons = emptyMap(),
            )

        assertThat(result.status).isEqualTo("empty")
        assertThat(result.probeBlockedReason).isNull()
    }

    @Test
    fun `missing_required_products when partial cache despite network failures on others`() {
        val networkFailures =
            mapOf(
                ProManager.BASE_PRODUCT_ID to "network_error",
                ProManager.MONTHLY_PRODUCT_ID to "network_error",
            )
        val result =
            resolveBillingProductCatalogStatus(
                billingReady = true,
                productDetailsSupported = true,
                requiredProductIds = required,
                cachedLogicalProductIds = setOf(ProManager.ELITE_PRODUCT_ID),
                productQueryFailureReasons = networkFailures,
            )

        assertThat(result.status).isEqualTo("missing_required_products")
        assertThat(result.probeBlockedReason).isNull()
    }
}
