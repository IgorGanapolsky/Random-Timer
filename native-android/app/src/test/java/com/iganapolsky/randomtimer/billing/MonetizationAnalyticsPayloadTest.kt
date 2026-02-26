package com.iganapolsky.randomtimer.billing

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.analytics.AnalyticsProperties
import org.junit.Test

class MonetizationAnalyticsPayloadTest {
    @Test
    fun `resultProperties keeps explicit entry point`() {
        val properties =
            MonetizationAnalyticsPayload.resultProperties(
                success = true,
                source = MonetizationSources.PAYWALL,
                entryPoint = "setup_upgrade_cta",
                responseCode = 0,
                debugMessage = "ok",
            )

        assertThat(properties[AnalyticsProperties.ENTRY_POINT]).isEqualTo("setup_upgrade_cta")
        assertThat(properties[AnalyticsProperties.SUCCESS]).isEqualTo(true)
        assertThat(properties[AnalyticsProperties.SOURCE]).isEqualTo(MonetizationSources.PAYWALL)
    }

    @Test
    fun `resultProperties falls back to source when entry point missing`() {
        val properties =
            MonetizationAnalyticsPayload.resultProperties(
                success = false,
                source = MonetizationSources.AUTO_RESTORE,
                entryPoint = null,
                responseCode = 2,
                debugMessage = null,
            )

        assertThat(properties[AnalyticsProperties.ENTRY_POINT]).isEqualTo(MonetizationSources.AUTO_RESTORE)
        assertThat(properties[AnalyticsProperties.DEBUG_MESSAGE]).isEqualTo("")
    }
}
