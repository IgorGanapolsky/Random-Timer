package com.iganapolsky.randomtimer.billing

import com.android.billingclient.api.BillingClient
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BillingResponseLabelsTest {
    @Test
    fun `labelFor maps FEATURE_NOT_SUPPORTED`() {
        assertEquals(
            "FEATURE_NOT_SUPPORTED",
            BillingResponseLabels.labelFor(BillingClient.BillingResponseCode.FEATURE_NOT_SUPPORTED),
        )
    }

    @Test
    fun `shouldRetryProductDetailsQuery allows transient codes under max attempts`() {
        assertTrue(
            BillingResponseLabels.shouldRetryProductDetailsQuery(
                BillingClient.BillingResponseCode.FEATURE_NOT_SUPPORTED,
                attempt = 1,
            ),
        )
    }

    @Test
    fun `shouldRetryProductDetailsQuery stops at max attempts`() {
        assertFalse(
            BillingResponseLabels.shouldRetryProductDetailsQuery(
                BillingClient.BillingResponseCode.FEATURE_NOT_SUPPORTED,
                attempt = 3,
            ),
        )
    }

    @Test
    fun `shouldRetryProductDetailsQuery ignores OK`() {
        assertFalse(
            BillingResponseLabels.shouldRetryProductDetailsQuery(
                BillingClient.BillingResponseCode.OK,
                attempt = 1,
            ),
        )
    }
}
