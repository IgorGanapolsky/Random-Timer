package com.iganapolsky.randomtimer.billing

internal data class BillingCatalogStatusResult(
    val status: String,
    val availableProductIds: List<String>,
    val missingProductIds: List<String>,
    val probeBlockedReason: String?,
)

/**
 * Maps cached Play catalog state to PostHog `billing_product_catalog_status.status`.
 * `empty` means billing was ready, product-details queries are supported, and Play returned no SKUs —
 * not "we could not run a catalog probe".
 */
internal fun resolveBillingProductCatalogStatus(
    billingReady: Boolean,
    productDetailsSupported: Boolean?,
    requiredProductIds: Set<String>,
    cachedLogicalProductIds: Set<String>,
    productQueryFailureReasons: Map<String, String> = emptyMap(),
): BillingCatalogStatusResult {
    if (!billingReady) {
        return blockedCatalogStatus(
            status = "billing_not_ready",
            reason = "billing_not_ready",
            requiredProductIds = requiredProductIds,
            cachedLogicalProductIds = cachedLogicalProductIds,
        )
    }
    if (productDetailsSupported != true) {
        val blockedStatus =
            if (productDetailsSupported == false) {
                "product_details_unsupported"
            } else {
                "catalog_probe_pending"
            }
        return blockedCatalogStatus(
            status = blockedStatus,
            reason = blockedStatus,
            requiredProductIds = requiredProductIds,
            cachedLogicalProductIds = cachedLogicalProductIds,
        )
    }

    val availableProductIds = cachedLogicalProductIds.intersect(requiredProductIds).sorted()
    val missingProductIds = requiredProductIds.minus(cachedLogicalProductIds).sorted()
    val catalogQueryBlockedReason =
        resolveCatalogQueryBlockedReason(
            requiredProductIds = requiredProductIds,
            cachedLogicalProductIds = cachedLogicalProductIds,
            productQueryFailureReasons = productQueryFailureReasons,
        )
    val status =
        when {
            catalogQueryBlockedReason != null -> "catalog_query_failed"
            availableProductIds.isEmpty() -> "empty"
            missingProductIds.isNotEmpty() -> "missing_required_products"
            else -> "ok"
        }
    return BillingCatalogStatusResult(
        status = status,
        availableProductIds = availableProductIds,
        missingProductIds = missingProductIds,
        probeBlockedReason = catalogQueryBlockedReason,
    )
}

/**
 * When every required SKU failed to load due to network error after retries, distinguish that
 * from Play returning an empty catalog (`empty`).
 */
internal fun resolveCatalogQueryBlockedReason(
    requiredProductIds: Set<String>,
    cachedLogicalProductIds: Set<String>,
    productQueryFailureReasons: Map<String, String>,
): String? {
    if (cachedLogicalProductIds.intersect(requiredProductIds).isNotEmpty()) {
        return null
    }
    val missingRequired = requiredProductIds.minus(cachedLogicalProductIds)
    if (missingRequired.isEmpty()) {
        return null
    }
    return if (missingRequired.all { productQueryFailureReasons[it] == "network_error" }) {
        "network_error"
    } else {
        null
    }
}

private fun blockedCatalogStatus(
    status: String,
    reason: String,
    requiredProductIds: Set<String>,
    cachedLogicalProductIds: Set<String>,
): BillingCatalogStatusResult {
    val availableProductIds = cachedLogicalProductIds.intersect(requiredProductIds).sorted()
    val missingProductIds = requiredProductIds.minus(cachedLogicalProductIds).sorted()
    return BillingCatalogStatusResult(
        status = status,
        availableProductIds = availableProductIds,
        missingProductIds = missingProductIds,
        probeBlockedReason = reason,
    )
}
