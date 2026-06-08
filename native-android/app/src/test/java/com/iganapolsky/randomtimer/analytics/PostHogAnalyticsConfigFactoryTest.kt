package com.iganapolsky.randomtimer.analytics

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PostHogAnalyticsConfigFactoryTest {
    @Test
    fun `error tracking autocapture enabled for production users`() {
        val config =
            PostHogAnalyticsConfigFactory.create(
                apiKey = "phc_test",
                isInternalUser = false,
            )
        assertTrue(config.errorTrackingConfig.autoCapture)
    }

    @Test
    fun `error tracking autocapture disabled for internal users`() {
        val config =
            PostHogAnalyticsConfigFactory.create(
                apiKey = "phc_test",
                isInternalUser = true,
            )
        assertFalse(config.errorTrackingConfig.autoCapture)
    }
}
