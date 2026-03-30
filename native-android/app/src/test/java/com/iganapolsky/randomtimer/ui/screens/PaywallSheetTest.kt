package com.iganapolsky.randomtimer.ui.screens

import org.junit.Assert.assertEquals
import org.junit.Test

class PaywallSheetTest {
    @Test
    fun `hidden unlock hold duration is eight seconds`() {
        assertEquals(8_000L, HIDDEN_UNLOCK_HOLD_DURATION_MS)
    }

    @Test
    fun `paywall copy focuses on training outcomes`() {
        assertEquals("Unlock Full Training Mode", PAYWALL_HEADLINE)
        assertEquals(
            "Longer sessions, voice coaching, more sounds, and repeatable rounds.",
            PAYWALL_SUBHEADLINE,
        )
        assertEquals(
            "Built for dry fire, sparring, drills, and reaction training.",
            PAYWALL_AUDIENCE_LINE,
        )
        assertEquals("One-time purchase. Unlock Pro forever.", PAYWALL_PRICING_FOOTER)
        assertEquals(
            listOf(
                "Train up to 60-minute sessions",
                "Get voice callouts during training",
                "Use loop mode with round limits",
                "Unlock the full sound library",
                "New Pro voice callouts and sound packs every 30 days",
            ),
            PAYWALL_FEATURE_ROWS,
        )
    }

    @Test
    fun `price label normalizes to yearly pricing`() {
        assertEquals("$29.99/year", normalizedPriceLabel("$29.99"))
        assertEquals("$29.99/yr", normalizedPriceLabel("$29.99/yr"))
    }
}
