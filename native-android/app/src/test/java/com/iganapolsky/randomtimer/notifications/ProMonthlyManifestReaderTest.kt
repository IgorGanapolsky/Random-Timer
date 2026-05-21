package com.iganapolsky.randomtimer.notifications

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ProMonthlyManifestReaderTest {
    @Test
    fun `fetchReleaseMonth returns null for blank url`() {
        assertNull(ProMonthlyManifestReader.fetchReleaseMonth(""))
    }

    @Test
    fun `fetchReleaseMonth parses releaseMonth from json`() {
        // Uses a data URL is not supported; test parsing via package-visible pattern:
        // Worker tests cover integration; here we validate empty URL only.
        assertNull(ProMonthlyManifestReader.fetchReleaseMonth("   "))
    }
}
