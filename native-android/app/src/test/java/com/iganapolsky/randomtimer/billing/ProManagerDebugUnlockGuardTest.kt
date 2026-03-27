package com.iganapolsky.randomtimer.billing

import org.junit.Assert.assertEquals
import org.junit.Test

class ProManagerDebugUnlockGuardTest {
    @Test
    fun `canUseDebugUnlock matches BuildConfig DEBUG`() {
        // In unit tests, BuildConfig.DEBUG is true
        assertEquals(com.iganapolsky.randomtimer.BuildConfig.DEBUG, ProManager.canUseDebugUnlock())
    }
}
