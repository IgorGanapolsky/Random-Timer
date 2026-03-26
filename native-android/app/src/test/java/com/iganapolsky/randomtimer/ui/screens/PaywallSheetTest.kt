package com.iganapolsky.randomtimer.ui.screens

import org.junit.Assert.assertEquals
import org.junit.Test

class PaywallSheetTest {
    @Test
    fun `hidden unlock hold duration is eight seconds`() {
        assertEquals(8_000L, HIDDEN_UNLOCK_HOLD_DURATION_MS)
    }
}
