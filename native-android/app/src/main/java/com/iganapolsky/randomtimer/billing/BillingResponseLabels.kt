package com.iganapolsky.randomtimer.billing

import com.android.billingclient.api.BillingClient

/** Human-readable Play Billing response codes for PostHog diagnostics. */
internal object BillingResponseLabels {
    fun labelFor(responseCode: Int): String =
        when (responseCode) {
            BillingClient.BillingResponseCode.OK -> "OK"
            BillingClient.BillingResponseCode.USER_CANCELED -> "USER_CANCELED"
            BillingClient.BillingResponseCode.SERVICE_UNAVAILABLE -> "SERVICE_UNAVAILABLE"
            BillingClient.BillingResponseCode.BILLING_UNAVAILABLE -> "BILLING_UNAVAILABLE"
            BillingClient.BillingResponseCode.ITEM_UNAVAILABLE -> "ITEM_UNAVAILABLE"
            BillingClient.BillingResponseCode.DEVELOPER_ERROR -> "DEVELOPER_ERROR"
            BillingClient.BillingResponseCode.ERROR -> "ERROR"
            BillingClient.BillingResponseCode.ITEM_ALREADY_OWNED -> "ITEM_ALREADY_OWNED"
            BillingClient.BillingResponseCode.ITEM_NOT_OWNED -> "ITEM_NOT_OWNED"
            BillingClient.BillingResponseCode.NETWORK_ERROR -> "NETWORK_ERROR"
            BillingClient.BillingResponseCode.SERVICE_DISCONNECTED -> "SERVICE_DISCONNECTED"
            BillingClient.BillingResponseCode.FEATURE_NOT_SUPPORTED -> "FEATURE_NOT_SUPPORTED"
            else -> "UNKNOWN_$responseCode"
        }

    /** Transient query failures worth retrying before emitting `billing_product_not_found`. */
    internal val retryableProductQueryResponseCodes: Set<Int> =
        setOf(
            BillingClient.BillingResponseCode.SERVICE_DISCONNECTED,
            BillingClient.BillingResponseCode.NETWORK_ERROR,
            BillingClient.BillingResponseCode.SERVICE_UNAVAILABLE,
            BillingClient.BillingResponseCode.FEATURE_NOT_SUPPORTED,
        )

    internal const val DEFAULT_PRODUCT_QUERY_MAX_ATTEMPTS: Int = 5

    internal fun shouldRetryProductDetailsQuery(
        responseCode: Int,
        attempt: Int,
        maxAttempts: Int = DEFAULT_PRODUCT_QUERY_MAX_ATTEMPTS,
    ): Boolean = attempt < maxAttempts && responseCode in retryableProductQueryResponseCodes

    /** Exponential backoff capped at 3.2s between catalog probe retries. */
    internal fun productQueryRetryDelayMs(
        attempt: Int,
        baseDelayMs: Long = 400L,
        maxDelayMs: Long = 3200L,
    ): Long {
        val exponent = (attempt - 1).coerceAtLeast(0)
        val scaled = baseDelayMs * (1L shl exponent.coerceAtMost(3))
        return scaled.coerceAtMost(maxDelayMs)
    }

    internal fun shouldReconnectBillingClient(responseCode: Int): Boolean =
        responseCode == BillingClient.BillingResponseCode.SERVICE_DISCONNECTED

    /** Caps `billing_product_query_retry` telemetry per logical SKU per session. */
    internal fun shouldEmitProductQueryRetryTelemetry(
        emittedCount: Int,
        maxPerSessionPerSku: Int = 3,
    ): Boolean = emittedCount < maxPerSessionPerSku
}
