package com.iganapolsky.randomtimer.notifications

import java.time.Month
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import java.util.Locale

/**
 * User-facing copy for monthly Pro audio drop reminders.
 * Release month uses ISO `yyyy-MM` from the hosted runtime manifest.
 */
object ProMonthlyContentMessaging {
    data class Copy(
        val title: String,
        val body: String,
    )

    fun monthLabel(releaseMonth: String): String {
        val trimmed = releaseMonth.trim()
        if (trimmed.isEmpty()) {
            return fallbackMonthLabel()
        }
        return try {
            YearMonth.parse(trimmed, DateTimeFormatter.ofPattern("yyyy-MM"))
                .format(DateTimeFormatter.ofPattern("MMMM yyyy", Locale.US))
        } catch (_: DateTimeParseException) {
            fallbackMonthLabel()
        }
    }

    fun notificationCopy(releaseMonth: String): Copy {
        val label = monthLabel(releaseMonth)
        return Copy(
            title = "New Audio Drops for $label",
            body = "Your Sound Arsenal has new tactical callouts. Open the app to train with the latest pack.",
        )
    }

    private fun fallbackMonthLabel(): String {
        val now = YearMonth.now()
        val monthName = Month.of(now.monthValue).getDisplayName(java.time.format.TextStyle.FULL, Locale.US)
        return "$monthName ${now.year}"
    }
}
