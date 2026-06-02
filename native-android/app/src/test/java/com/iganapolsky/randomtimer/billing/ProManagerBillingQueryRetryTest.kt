package com.iganapolsky.randomtimer.billing

import com.android.billingclient.api.BillingClient
import org.junit.Assert.assertTrue
import org.junit.Test

class ProManagerBillingQueryRetryTest {
    @Test
    fun `catalog retry set includes service disconnected`() {
        assertTrue(
            BillingResponseLabels.retryableProductQueryResponseCodes.contains(
                BillingClient.BillingResponseCode.SERVICE_DISCONNECTED,
            ),
        )
    }
}
