package com.iganapolsky.randomtimer.billing

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ProManagerDebugUnlockGuardTest {
    @Test
    fun `canUseDebugUnlock returns true in debug builds`() {
        assertTrue(ProManager.canUseDebugUnlock(isDebugBuild = true))
    }

    @Test
    fun `canUseDebugUnlock returns false in release builds`() {
        assertFalse(ProManager.canUseDebugUnlock(isDebugBuild = false))
    }
}
