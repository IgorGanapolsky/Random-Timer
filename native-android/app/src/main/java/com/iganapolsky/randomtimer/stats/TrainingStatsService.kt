package com.iganapolsky.randomtimer.stats

import android.content.Context
import android.content.SharedPreferences
import java.time.LocalDate
import java.time.temporal.ChronoUnit

class TrainingStatsService(
    context: Context,
) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("training_stats", Context.MODE_PRIVATE)

    val totalSessions: Int get() = prefs.getInt("total_sessions", 0)
    val currentStreak: Int get() = prefs.getInt("streak", 0)

    fun recordSession() {
        val total = totalSessions + 1
        prefs.edit().putInt("total_sessions", total).apply()

        val today = LocalDate.now()
        val lastDateStr = prefs.getString("last_date", null)
        val lastDate = lastDateStr?.let { LocalDate.parse(it) }

        if (lastDate != null) {
            val daysBetween = ChronoUnit.DAYS.between(lastDate, today)
            when {
                daysBetween == 1L -> prefs.edit().putInt("streak", currentStreak + 1).apply()
                daysBetween > 1L -> prefs.edit().putInt("streak", 1).apply()
            }
        } else {
            prefs.edit().putInt("streak", 1).apply()
        }

        prefs.edit().putString("last_date", today.toString()).apply()
    }
}
