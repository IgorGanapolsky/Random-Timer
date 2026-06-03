package com.iganapolsky.randomtimer.billing

import com.android.billingclient.api.BillingClient
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class BillingProductQueryPlanTest {
    @Test
    fun `paywall catalog dedupes monthly to elite subs probe`() {
        val specs = buildPaywallCatalogQuerySpecs()

        assertThat(specs).hasSize(2)
        assertThat(specs.map { it.billingProductId }).containsExactly(
            ProManager.BASE_PRODUCT_ID,
            ProManager.ELITE_PRODUCT_ID,
        )
        assertThat(specs.count { it.productType == BillingClient.ProductType.SUBS }).isEqualTo(1)
    }

    @Test
    fun `group specs by product type for batched fetch`() {
        val grouped = groupPaywallCatalogSpecsByProductType(buildPaywallCatalogQuerySpecs())

        assertThat(grouped.keys).containsExactly(
            BillingClient.ProductType.INAPP,
            BillingClient.ProductType.SUBS,
        )
        assertThat(grouped[BillingClient.ProductType.INAPP]).hasSize(1)
        assertThat(grouped[BillingClient.ProductType.SUBS]).hasSize(1)
    }

    @Test
    fun `logical ids for play product include monthly alias`() {
        val specs = buildPaywallCatalogQuerySpecs()
        val logicalIds =
            logicalProductIdsForPlayProduct(
                specs,
                ProManager.ELITE_PRODUCT_ID,
            )

        assertThat(logicalIds).containsExactly(
            ProManager.ELITE_PRODUCT_ID,
            ProManager.MONTHLY_PRODUCT_ID,
        )
    }

    @Test
    fun `productQueryRetryDelayMs grows with attempt capped`() {
        assertThat(BillingResponseLabels.productQueryRetryDelayMs(attempt = 1)).isEqualTo(400L)
        assertThat(BillingResponseLabels.productQueryRetryDelayMs(attempt = 3)).isEqualTo(1600L)
        assertThat(BillingResponseLabels.productQueryRetryDelayMs(attempt = 10)).isEqualTo(3200L)
    }
}
