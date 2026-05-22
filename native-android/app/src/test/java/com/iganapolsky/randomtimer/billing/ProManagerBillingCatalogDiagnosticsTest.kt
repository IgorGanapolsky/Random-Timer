package com.iganapolsky.randomtimer.billing

import com.iganapolsky.randomtimer.analytics.AndroidInstallChannel
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ProManagerBillingCatalogDiagnosticsTest {
    @Test
    fun `should not report when billing is not ready`() {
        assertFalse(
            ProManager.shouldReportBillingProductNotFound(
                billingReady = false,
                distributionChannel = AndroidInstallChannel.PLAY_STORE,
                alreadyReported = emptySet(),
                productId = ProManager.BASE_PRODUCT_ID,
            ),
        )
    }

    @Test
    fun `should not report for non-play installs`() {
        assertFalse(
            ProManager.shouldReportBillingProductNotFound(
                billingReady = true,
                distributionChannel = AndroidInstallChannel.NON_PLAY_INSTALL,
                alreadyReported = emptySet(),
                productId = ProManager.ELITE_PRODUCT_ID,
            ),
        )
    }

    @Test
    fun `should not report duplicate product in same session`() {
        assertFalse(
            ProManager.shouldReportBillingProductNotFound(
                billingReady = true,
                distributionChannel = AndroidInstallChannel.PLAY_STORE,
                alreadyReported = setOf(ProManager.MONTHLY_PRODUCT_ID),
                productId = ProManager.MONTHLY_PRODUCT_ID,
            ),
        )
    }

    @Test
    fun `should report for play store when billing ready and first time`() {
        assertTrue(
            ProManager.shouldReportBillingProductNotFound(
                billingReady = true,
                distributionChannel = AndroidInstallChannel.PLAY_STORE,
                alreadyReported = emptySet(),
                productId = ProManager.MONTHLY_PRODUCT_ID,
            ),
        )
    }

    @Test
    fun `should report for legacy channel when billing ready`() {
        assertTrue(
            ProManager.shouldReportBillingProductNotFound(
                billingReady = true,
                distributionChannel = "legacy",
                alreadyReported = emptySet(),
                productId = ProManager.BASE_PRODUCT_ID,
            ),
        )
    }
}
