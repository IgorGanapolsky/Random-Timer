package com.iganapolsky.randomtimer.billing

import com.android.billingclient.api.BillingClient

/**
 * Legacy SKU catalog path when [BillingClient.FeatureType.PRODUCT_DETAILS] is unsupported.
 *
 * Play Billing Library 7 removed [BillingClient.querySkuDetailsAsync]; on unsupported devices we
 * still attempt [queryProductDetails] (Play may serve backward-compatible SKU payloads) and map
 * results into the same logical paywall catalog cache used by the modern path.
 */
internal fun shouldAttemptLegacySkuCatalogProbe(productDetailsSupported: Boolean?): Boolean =
    productDetailsSupported == false

internal fun logicalProductIdsResolvedFromLegacySkuQuery(
    specs: List<BillingProductQuerySpec>,
    foundBillingProductIds: List<String>,
): Set<String> {
    val found = foundBillingProductIds.toSet()
    return specs
        .filter { spec -> spec.billingProductId in found }
        .map { it.logicalProductId }
        .toSet()
}

internal fun isLegacySkuCatalogDegraded(
    billingResponseCode: Int,
    foundBillingProductIds: List<String>,
): Boolean =
    foundBillingProductIds.isEmpty() &&
        (
            billingResponseCode == BillingClient.BillingResponseCode.FEATURE_NOT_SUPPORTED ||
                billingResponseCode == BillingClient.BillingResponseCode.BILLING_UNAVAILABLE
        )
