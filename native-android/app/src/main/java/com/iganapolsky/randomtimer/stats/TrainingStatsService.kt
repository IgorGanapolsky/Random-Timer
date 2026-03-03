package com.iganapolsky.randomtimer.stats

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.WorkoutSession
import org.json.JSONArray
import org.json.JSONObject
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

    fun recordWorkoutSession(session: WorkoutSession) {
        val sessions = getWorkoutSessionsMutable()
        sessions.add(0, session)

        // Keep max 100 sessions (trim oldest when over limit)
        while (sessions.size > MAX_SESSIONS) {
            sessions.removeAt(sessions.size - 1)
        }

        saveWorkoutSessions(sessions)
    }

    fun getWorkoutSessions(): List<WorkoutSession> = getWorkoutSessionsMutable()

    fun getTotalTrainingTimeSeconds(): Long =
        getWorkoutSessions()
            .filter { it.completed }
            .sumOf { it.targetDurationSeconds.toLong() }

    private fun getWorkoutSessionsMutable(): MutableList<WorkoutSession> {
        val jsonString = prefs.getString(KEY_WORKOUT_SESSIONS, null) ?: return mutableListOf()
        return try {
            val jsonArray = JSONArray(jsonString)
            val sessions = mutableListOf<WorkoutSession>()
            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.getJSONObject(i)
                sessions.add(
                    WorkoutSession(
                        id = obj.getString("id"),
                        timestamp = obj.getLong("timestamp"),
                        targetDurationSeconds = obj.getInt("targetDurationSeconds"),
                        soundType =
                            try {
                                SoundType.valueOf(obj.getString("soundType"))
                            } catch (_: Exception) {
                                SoundType.INTENSE
                            },
                        completed = obj.getBoolean("completed"),
                    ),
                )
            }
            sessions
        } catch (e: Exception) {
            Log.w("TrainingStatsService", "Failed to parse workout sessions", e)
            mutableListOf()
        }
    }

    private fun saveWorkoutSessions(sessions: List<WorkoutSession>) {
        val jsonArray = JSONArray()
        for (session in sessions) {
            val obj =
                JSONObject().apply {
                    put("id", session.id)
                    put("timestamp", session.timestamp)
                    put("targetDurationSeconds", session.targetDurationSeconds)
                    put("soundType", session.soundType.name)
                    put("completed", session.completed)
                }
            jsonArray.put(obj)
        }
        prefs.edit().putString(KEY_WORKOUT_SESSIONS, jsonArray.toString()).apply()
    }

    companion object {
        private const val KEY_WORKOUT_SESSIONS = "workout_sessions"
        private const val MAX_SESSIONS = 100
    }
}
