package com.iganapolsky.randomtimer.ui.screens

internal const val PAYWALL_BILLING_REFRESH_MAX_ATTEMPTS = 12
internal const val PAYWALL_BILLING_REFRESH_DELAY_MS = 500L

internal data class PaywallBillingSnapshot(
    val catalogProbed: Boolean,
    val billingReady: Boolean,
    val availableProductIds: Set<String>,
)

internal fun shouldContinuePaywallBillingRefresh(
    snapshot: PaywallBillingSnapshot,
    attempt: Int,
    maxAttempts: Int = PAYWALL_BILLING_REFRESH_MAX_ATTEMPTS,
): Boolean {
    if (attempt >= maxAttempts) {
        return false
    }
    return !hasPurchasablePaywallPlan(
        availableProductIds = snapshot.availableProductIds,
        billingCatalogProbed = snapshot.catalogProbed,
        billingReady = snapshot.billingReady,
    )
}
