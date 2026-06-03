package com.iganapolsky.randomtimer.billing

import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.QueryProductDetailsParams

internal data class BillingProductQuerySpec(
    val logicalProductId: String,
    val billingProductId: String,
    val productType: String,
)

/** Deduplicated Play catalog probes for paywall SKUs (monthly shares elite_tactical). */
internal fun buildPaywallCatalogQuerySpecs(
    logicalProductIds: List<String> = paywallCatalogLogicalProductIds(),
): List<BillingProductQuerySpec> =
    logicalProductIds
        .map { logicalProductId ->
            BillingProductQuerySpec(
                logicalProductId = logicalProductId,
                billingProductId = playBillingProductId(logicalProductId),
                productType = billingProductTypeForLogicalProductId(logicalProductId),
            )
        }.distinctBy { spec -> spec.billingProductId to spec.productType }

internal fun paywallCatalogLogicalProductIds(): List<String> =
    listOf(
        ProManager.BASE_PRODUCT_ID,
        ProManager.ELITE_PRODUCT_ID,
        ProManager.MONTHLY_PRODUCT_ID,
    )

internal fun buildQueryProductDetailsParams(
    productType: String,
    billingProductIds: List<String>,
): QueryProductDetailsParams {
    val productList =
        billingProductIds.map { billingProductId ->
            QueryProductDetailsParams.Product
                .newBuilder()
                .setProductId(billingProductId)
                .setProductType(productType)
                .build()
        }
    return QueryProductDetailsParams
        .newBuilder()
        .setProductList(productList)
        .build()
}

internal fun groupPaywallCatalogSpecsByProductType(
    specs: List<BillingProductQuerySpec>,
): Map<String, List<BillingProductQuerySpec>> = specs.groupBy { it.productType }

internal fun logicalProductIdsForPlayProduct(
    specs: List<BillingProductQuerySpec>,
    billingProductId: String,
): List<String> = specs.filter { it.billingProductId == billingProductId }.map { it.logicalProductId }

internal fun paywallCatalogProductTypesInFetchOrder(): List<String> =
    listOf(
        BillingClient.ProductType.INAPP,
        BillingClient.ProductType.SUBS,
    )
