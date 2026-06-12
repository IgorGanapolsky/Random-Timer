package com.iganapolsky.randomtimer.billing

import com.android.billingclient.api.BillingClient
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class BillingProductQueryPlanTest {
    @Test
    fun `paywall catalog probes each Play subscription product id`() {
        val specs = buildPaywallCatalogQuerySpecs()

        assertThat(specs).hasSize(3)
        assertThat(specs.map { it.billingProductId }).containsExactly(
            ProManager.BASE_PRODUCT_ID,
            ProManager.ELITE_PRODUCT_ID,
            ProManager.MONTHLY_PRODUCT_ID,
        )
        assertThat(specs.count { it.productType == BillingClient.ProductType.SUBS }).isEqualTo(2)
    }

    @Test
    fun `group specs by product type for batched fetch`() {
        val grouped = groupPaywallCatalogSpecsByProductType(buildPaywallCatalogQuerySpecs())

        assertThat(grouped.keys).containsExactly(
            BillingClient.ProductType.INAPP,
            BillingClient.ProductType.SUBS,
        )
        assertThat(grouped[BillingClient.ProductType.INAPP]).hasSize(1)
        assertThat(grouped[BillingClient.ProductType.SUBS]).hasSize(2)
    }

    @Test
    fun `deduped specs expose single logical id per play product`() {
        val specs = buildPaywallCatalogQuerySpecs()
        val eliteLogicalIds =
            logicalProductIdsForPlayProduct(
                specs,
                ProManager.ELITE_PRODUCT_ID,
            )

        assertThat(eliteLogicalIds).containsExactly(ProManager.ELITE_PRODUCT_ID)
        assertThat(playBillingProductId(ProManager.MONTHLY_PRODUCT_ID))
            .isEqualTo(ProManager.MONTHLY_PRODUCT_ID)
    }

    @Test
    fun `productQueryRetryDelayMs grows with attempt capped`() {
        assertThat(BillingResponseLabels.productQueryRetryDelayMs(attempt = 1)).isEqualTo(400L)
        assertThat(BillingResponseLabels.productQueryRetryDelayMs(attempt = 3)).isEqualTo(1600L)
        assertThat(BillingResponseLabels.productQueryRetryDelayMs(attempt = 10)).isEqualTo(3200L)
    }
}
