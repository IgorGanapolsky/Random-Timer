package com.iganapolsky.randomtimer.stats

import android.content.Context
import android.content.SharedPreferences
import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.WorkoutSession
import io.mockk.*
import org.junit.Before
import org.junit.Test

/**
 * Unit tests for [TrainingStatsService].
 *
 * Android's [SharedPreferences] is mocked with an in-memory map so these run
 * on the JVM without requiring a device or Robolectric.
 */
class TrainingStatsServiceTest {
    private lateinit var service: TrainingStatsService
    private lateinit var fakePrefs: FakeSharedPreferences

    @Before
    fun setUp() {
        fakePrefs = FakeSharedPreferences()
        val context = mockk<Context>()
        every { context.getSharedPreferences(any(), any()) } returns fakePrefs
        service = TrainingStatsService(context)
    }

    // ─── totalSessions ────────────────────────────────────────────────────────

    @Test
    fun `totalSessions starts at zero on fresh prefs`() {
        assertThat(service.totalSessions).isEqualTo(0)
    }

    @Test
    fun `recordSession increments totalSessions by one`() {
        service.recordSession()
        assertThat(service.totalSessions).isEqualTo(1)
    }

    @Test
    fun `recordSession increments totalSessions across multiple calls`() {
        repeat(5) { service.recordSession() }
        assertThat(service.totalSessions).isEqualTo(5)
    }

    // ─── streak ───────────────────────────────────────────────────────────────

    @Test
    fun `currentStreak starts at zero`() {
        assertThat(service.currentStreak).isEqualTo(0)
    }

    @Test
    fun `first recordSession sets streak to one`() {
        service.recordSession()
        assertThat(service.currentStreak).isEqualTo(1)
    }

    @Test
    fun `same-day repeated sessions do not increase streak beyond one`() {
        // Both calls happen on the same LocalDate.now()
        service.recordSession()
        service.recordSession()
        // streak stays at 1 — daysBetween == 0, neither branch fires
        assertThat(service.currentStreak).isEqualTo(1)
    }

    // ─── getWorkoutSessions ───────────────────────────────────────────────────

    @Test
    fun `getWorkoutSessions returns empty list when nothing recorded`() {
        assertThat(service.getWorkoutSessions()).isEmpty()
    }

    @Test
    fun `recordWorkoutSession stores a single session`() {
        val session =
            WorkoutSession(
                id = "abc-123",
                timestamp = 1_000_000L,
                targetDurationSeconds = 60,
                soundType = SoundType.INTENSE,
                completed = true,
            )

        service.recordWorkoutSession(session)

        val stored = service.getWorkoutSessions()
        assertThat(stored).hasSize(1)
        assertThat(stored[0].id).isEqualTo("abc-123")
        assertThat(stored[0].targetDurationSeconds).isEqualTo(60)
        assertThat(stored[0].completed).isTrue()
    }

    @Test
    fun `recordWorkoutSession prepends new sessions (most recent first)`() {
        val first =
            WorkoutSession(
                id = "first",
                timestamp = 1_000L,
                targetDurationSeconds = 30,
                soundType = SoundType.GENTLE,
                completed = true,
            )
        val second =
            WorkoutSession(
                id = "second",
                timestamp = 2_000L,
                targetDurationSeconds = 60,
                soundType = SoundType.INTENSE,
                completed = false,
            )

        service.recordWorkoutSession(first)
        service.recordWorkoutSession(second)

        val stored = service.getWorkoutSessions()
        assertThat(stored[0].id).isEqualTo("second")
        assertThat(stored[1].id).isEqualTo("first")
    }

    @Test
    fun `recordWorkoutSession preserves all SoundType values`() {
        val session =
            WorkoutSession(
                id = "gong-session",
                timestamp = 500L,
                targetDurationSeconds = 90,
                soundType = SoundType.GONG,
                completed = true,
            )

        service.recordWorkoutSession(session)

        val stored = service.getWorkoutSessions()
        assertThat(stored[0].soundType).isEqualTo(SoundType.GONG)
    }

    @Test
    fun `recordWorkoutSession falls back to INTENSE for unknown sound type in persisted JSON`() {
        // Inject raw JSON with an unknown soundType string to simulate forward-compat scenario
        val brokenJson = """[{"id":"x","timestamp":1,"targetDurationSeconds":10,"soundType":"NONEXISTENT","completed":false}]"""
        fakePrefs.rawPut("workout_sessions", brokenJson)

        val stored = service.getWorkoutSessions()

        assertThat(stored).hasSize(1)
        assertThat(stored[0].soundType).isEqualTo(SoundType.INTENSE)
    }

    @Test
    fun `getWorkoutSessions returns empty list when JSON is malformed`() {
        fakePrefs.rawPut("workout_sessions", "NOT_VALID_JSON")

        val stored = service.getWorkoutSessions()

        assertThat(stored).isEmpty()
    }

    @Test
    fun `recordWorkoutSession caps list at 100 entries`() {
        // Record 105 sessions
        for (i in 1..105) {
            service.recordWorkoutSession(
                WorkoutSession(
                    id = "session-$i",
                    timestamp = i.toLong(),
                    targetDurationSeconds = 30,
                    soundType = SoundType.INTENSE,
                    completed = true,
                ),
            )
        }

        val stored = service.getWorkoutSessions()
        assertThat(stored).hasSize(100)
    }

    @Test
    fun `recordWorkoutSession keeps most recent 100 when over cap`() {
        for (i in 1..105) {
            service.recordWorkoutSession(
                WorkoutSession(
                    id = "session-$i",
                    timestamp = i.toLong(),
                    targetDurationSeconds = 30,
                    soundType = SoundType.INTENSE,
                    completed = true,
                ),
            )
        }

        val stored = service.getWorkoutSessions()
        // First element should be the last recorded (most recent)
        assertThat(stored[0].id).isEqualTo("session-105")
        // 100th element should be session-6 (105 - 100 + 1 = 6)
        assertThat(stored[99].id).isEqualTo("session-6")
    }

    // ─── getTotalTrainingTimeSeconds ──────────────────────────────────────────

    @Test
    fun `getTotalTrainingTimeSeconds returns zero when no sessions recorded`() {
        assertThat(service.getTotalTrainingTimeSeconds()).isEqualTo(0L)
    }

    @Test
    fun `getTotalTrainingTimeSeconds sums completed session durations`() {
        service.recordWorkoutSession(
            WorkoutSession(id = "a", timestamp = 1L, targetDurationSeconds = 120, soundType = SoundType.INTENSE, completed = true),
        )
        service.recordWorkoutSession(
            WorkoutSession(id = "b", timestamp = 2L, targetDurationSeconds = 180, soundType = SoundType.GENTLE, completed = true),
        )

        assertThat(service.getTotalTrainingTimeSeconds()).isEqualTo(300L)
    }

    @Test
    fun `getTotalTrainingTimeSeconds excludes incomplete sessions`() {
        service.recordWorkoutSession(
            WorkoutSession(id = "done", timestamp = 1L, targetDurationSeconds = 60, soundType = SoundType.INTENSE, completed = true),
        )
        service.recordWorkoutSession(
            WorkoutSession(id = "abandoned", timestamp = 2L, targetDurationSeconds = 300, soundType = SoundType.INTENSE, completed = false),
        )

        assertThat(service.getTotalTrainingTimeSeconds()).isEqualTo(60L)
    }

    @Test
    fun `getTotalTrainingTimeSeconds returns zero when all sessions incomplete`() {
        repeat(3) { i ->
            service.recordWorkoutSession(
                WorkoutSession(
                    id = "session-$i",
                    timestamp = i.toLong(),
                    targetDurationSeconds = 90,
                    soundType = SoundType.INTENSE,
                    completed = false,
                ),
            )
        }

        assertThat(service.getTotalTrainingTimeSeconds()).isEqualTo(0L)
    }
}

// ─── In-memory SharedPreferences ──────────────────────────────────────────────

/**
 * Simple in-memory [SharedPreferences] implementation for unit tests.
 * Avoids a Robolectric dependency while keeping tests fast.
 */
private class FakeSharedPreferences : SharedPreferences {
    private val data = mutableMapOf<String, Any?>()

    /** Bypass the normal put APIs to inject raw strings (for error-path tests). */
    fun rawPut(
        key: String,
        value: String,
    ) {
        data[key] = value
    }

    override fun getAll(): Map<String, *> = data.toMap()

    override fun getString(
        key: String,
        defValue: String?,
    ) = data[key] as? String ?: defValue

    override fun getStringSet(
        key: String,
        defValues: Set<String>?,
    ) = data[key] as? Set<String> ?: defValues

    override fun getInt(
        key: String,
        defValue: Int,
    ) = (data[key] as? Int) ?: defValue

    override fun getLong(
        key: String,
        defValue: Long,
    ) = (data[key] as? Long) ?: defValue

    override fun getFloat(
        key: String,
        defValue: Float,
    ) = (data[key] as? Float) ?: defValue

    override fun getBoolean(
        key: String,
        defValue: Boolean,
    ) = (data[key] as? Boolean) ?: defValue

    override fun contains(key: String) = data.containsKey(key)

    override fun edit(): SharedPreferences.Editor = FakeEditor(data)

    override fun registerOnSharedPreferenceChangeListener(listener: SharedPreferences.OnSharedPreferenceChangeListener?) = Unit

    override fun unregisterOnSharedPreferenceChangeListener(listener: SharedPreferences.OnSharedPreferenceChangeListener?) = Unit
}

private class FakeEditor(
    private val data: MutableMap<String, Any?>,
) : SharedPreferences.Editor {
    private val pending = mutableMapOf<String, Any?>()
    private val removals = mutableSetOf<String>()
    private var clearAll = false

    override fun putString(
        key: String,
        value: String?,
    ) = apply { pending[key] = value }

    override fun putStringSet(
        key: String,
        values: Set<String>?,
    ) = apply { pending[key] = values }

    override fun putInt(
        key: String,
        value: Int,
    ) = apply { pending[key] = value }

    override fun putLong(
        key: String,
        value: Long,
    ) = apply { pending[key] = value }

    override fun putFloat(
        key: String,
        value: Float,
    ) = apply { pending[key] = value }

    override fun putBoolean(
        key: String,
        value: Boolean,
    ) = apply { pending[key] = value }

    override fun remove(key: String) = apply { removals.add(key) }

    override fun clear() = apply { clearAll = true }

    override fun commit(): Boolean {
        applyChanges()
        return true
    }

    override fun apply() {
        applyChanges()
    }

    private fun applyChanges() {
        if (clearAll) data.clear()
        removals.forEach { data.remove(it) }
        data.putAll(pending)
    }
}
