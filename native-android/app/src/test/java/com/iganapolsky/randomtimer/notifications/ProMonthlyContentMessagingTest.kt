package com.iganapolsky.randomtimer.notifications

import org.junit.Assert.assertEquals
import org.junit.Test

class ProMonthlyContentMessagingTest {
    @Test
    fun `monthLabel formats yyyy-MM as full month and year`() {
        assertEquals("May 2026", ProMonthlyContentMessaging.monthLabel("2026-05"))
    }

    @Test
    fun `notificationCopy uses release month in title`() {
        val copy = ProMonthlyContentMessaging.notificationCopy("2026-05")
        assertEquals("New Audio Drops for May 2026", copy.title)
        assert(copy.body.contains("Sound Arsenal"))
    }
}
