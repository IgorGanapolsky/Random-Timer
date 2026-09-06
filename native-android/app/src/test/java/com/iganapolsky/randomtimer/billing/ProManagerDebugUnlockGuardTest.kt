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
    fun `canUseDebugUnlock returns true in release builds`() {
        assertTrue(ProManager.canUseDebugUnlock(isDebugBuild = false))
    }

    @Test
    fun `auto restore applies when debug override inactive`() {
        assertTrue(ProManager.shouldApplyAutoRestoreEntitlement(debugOverrideActive = false))
    }

    @Test
    fun `auto restore skips when debug override active`() {
        assertFalse(ProManager.shouldApplyAutoRestoreEntitlement(debugOverrideActive = true))
    }
}
