package com.iganapolsky.randomtimer.ui.components

import org.junit.Assert.assertEquals
import org.junit.Test

class PrimaryButtonLabelTest {
    @Test
    fun `nonBlankButtonLabel defaults when blank`() {
        assertEquals("Continue", nonBlankButtonLabel(""))
        assertEquals("Continue", nonBlankButtonLabel("   "))
        assertEquals("Continue", nonBlankButtonLabel("\t\n"))
    }

    @Test
    fun `nonBlankButtonLabel preserves trimmed copy`() {
        assertEquals("Start Monthly", nonBlankButtonLabel("  Start Monthly  "))
    }
}
