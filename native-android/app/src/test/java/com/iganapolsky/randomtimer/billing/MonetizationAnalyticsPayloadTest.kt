package com.iganapolsky.randomtimer.billing

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.analytics.AnalyticsProperties
import org.junit.Test

class MonetizationAnalyticsPayloadTest {
    @Test
    fun `attemptProperties includes product and explicit entry point`() {
        val properties =
            MonetizationAnalyticsPayload.attemptProperties(
                source = MonetizationSources.PAYWALL,
                entryPoint = "setup_upgrade_cta",
                productID = "pro_base",
            )

        assertThat(properties[AnalyticsProperties.ENTRY_POINT]).isEqualTo("setup_upgrade_cta")
        assertThat(properties[AnalyticsProperties.SOURCE]).isEqualTo(MonetizationSources.PAYWALL)
        assertThat(properties[AnalyticsProperties.PRODUCT_ID]).isEqualTo("pro_base")
    }

    @Test
    fun `successProperties falls back entry point and carries response metadata`() {
        val properties =
            MonetizationAnalyticsPayload.successProperties(
                source = MonetizationSources.BILLING_CALLBACK,
                entryPoint = null,
                productID = "elite_tactical",
                responseCode = 0,
                debugMessage = "ok",
            )

        assertThat(properties[AnalyticsProperties.ENTRY_POINT]).isEqualTo(MonetizationSources.BILLING_CALLBACK)
        assertThat(properties[AnalyticsProperties.SOURCE]).isEqualTo(MonetizationSources.BILLING_CALLBACK)
        assertThat(properties[AnalyticsProperties.SUCCESS]).isEqualTo(true)
        assertThat(properties[AnalyticsProperties.RESPONSE_CODE]).isEqualTo(0)
        assertThat(properties[AnalyticsProperties.DEBUG_MESSAGE]).isEqualTo("ok")
        assertThat(properties[AnalyticsProperties.PRODUCT_ID]).isEqualTo("elite_tactical")
    }

    @Test
    fun `resultProperties keeps explicit entry point`() {
        val properties =
            MonetizationAnalyticsPayload.resultProperties(
                success = true,
                result = "success",
                source = MonetizationSources.PAYWALL,
                entryPoint = "setup_upgrade_cta",
                responseCode = 0,
                debugMessage = "ok",
            )

        assertThat(properties[AnalyticsProperties.ENTRY_POINT]).isEqualTo("setup_upgrade_cta")
        assertThat(properties[AnalyticsProperties.RESULT]).isEqualTo("success")
        assertThat(properties[AnalyticsProperties.SUCCESS]).isEqualTo(true)
        assertThat(properties[AnalyticsProperties.SOURCE]).isEqualTo(MonetizationSources.PAYWALL)
    }

    @Test
    fun `resultProperties falls back to source when entry point missing`() {
        val properties =
            MonetizationAnalyticsPayload.resultProperties(
                success = false,
                result = "failed",
                source = MonetizationSources.AUTO_RESTORE,
                entryPoint = null,
                responseCode = 2,
                debugMessage = null,
            )

        assertThat(properties[AnalyticsProperties.ENTRY_POINT]).isEqualTo(MonetizationSources.AUTO_RESTORE)
        assertThat(properties[AnalyticsProperties.RESULT]).isEqualTo("failed")
        assertThat(properties[AnalyticsProperties.DEBUG_MESSAGE]).isEqualTo("")
    }

    @Test
    fun `resultProperties includes product id and failure reason when provided`() {
        val properties =
            MonetizationAnalyticsPayload.resultProperties(
                success = false,
                result = "failed",
                source = MonetizationSources.PAYWALL,
                entryPoint = "setup_upgrade_cta",
                responseCode = 4,
                debugMessage = "item unavailable",
                productId = "elite_tactical_monthly",
                reason = "item_unavailable",
            )

        assertThat(properties[AnalyticsProperties.PRODUCT_ID]).isEqualTo("elite_tactical_monthly")
        assertThat(properties[AnalyticsProperties.REASON]).isEqualTo("item_unavailable")
        assertThat(properties[AnalyticsProperties.RESULT]).isEqualTo("failed")
        assertThat(properties[AnalyticsProperties.SUCCESS]).isEqualTo(false)
    }

    @Test
    fun `resultProperties omits reason on success`() {
        val properties =
            MonetizationAnalyticsPayload.resultProperties(
                success = true,
                result = "success",
                source = MonetizationSources.PAYWALL,
                entryPoint = "setup_upgrade_cta",
                responseCode = 0,
                debugMessage = null,
                productId = "pro_base",
                reason = null,
            )

        assertThat(properties[AnalyticsProperties.PRODUCT_ID]).isEqualTo("pro_base")
        assertThat(properties).doesNotContainKey(AnalyticsProperties.REASON)
    }
}
