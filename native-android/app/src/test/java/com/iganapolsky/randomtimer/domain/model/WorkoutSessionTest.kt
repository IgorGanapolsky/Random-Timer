package com.iganapolsky.randomtimer.domain.model

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class WorkoutSessionTest {

    @Test
    fun `session auto-generates non-blank uuid id when not provided`() {
        val session = WorkoutSession(
            targetDurationSeconds = 60,
            soundType = SoundType.INTENSE,
            completed = true,
        )

        assertThat(session.id).isNotEmpty()
        // UUID format: 8-4-4-4-12
        assertThat(session.id).matches("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
    }

    @Test
    fun `two sessions with default ids have unique ids`() {
        val a = WorkoutSession(targetDurationSeconds = 60, soundType = SoundType.INTENSE, completed = true)
        val b = WorkoutSession(targetDurationSeconds = 60, soundType = SoundType.INTENSE, completed = true)

        assertThat(a.id).isNotEqualTo(b.id)
    }

    @Test
    fun `session auto-sets timestamp close to current time`() {
        val before = System.currentTimeMillis()
        val session = WorkoutSession(
            targetDurationSeconds = 60,
            soundType = SoundType.GENTLE,
            completed = false,
        )
        val after = System.currentTimeMillis()

        assertThat(session.timestamp).isAtLeast(before)
        assertThat(session.timestamp).isAtMost(after)
    }

    @Test
    fun `session accepts explicit id and timestamp`() {
        val session = WorkoutSession(
            id = "explicit-id-123",
            timestamp = 1700000000000L,
            targetDurationSeconds = 120,
            soundType = SoundType.BUZZER,
            completed = true,
        )

        assertThat(session.id).isEqualTo("explicit-id-123")
        assertThat(session.timestamp).isEqualTo(1700000000000L)
    }

    @Test
    fun `completed session stores completed as true`() {
        val session = WorkoutSession(
            targetDurationSeconds = 180,
            soundType = SoundType.GONG,
            completed = true,
        )

        assertThat(session.completed).isTrue()
    }

    @Test
    fun `incomplete session stores completed as false`() {
        val session = WorkoutSession(
            targetDurationSeconds = 180,
            soundType = SoundType.INTENSE,
            completed = false,
        )

        assertThat(session.completed).isFalse()
    }

    @Test
    fun `data class equality holds for identical explicit sessions`() {
        val a = WorkoutSession(
            id = "same-id",
            timestamp = 1000L,
            targetDurationSeconds = 90,
            soundType = SoundType.WHISTLE,
            completed = true,
        )
        val b = WorkoutSession(
            id = "same-id",
            timestamp = 1000L,
            targetDurationSeconds = 90,
            soundType = SoundType.WHISTLE,
            completed = true,
        )

        assertThat(a).isEqualTo(b)
        assertThat(a.hashCode()).isEqualTo(b.hashCode())
    }

    @Test
    fun `data class inequality when completed differs`() {
        val base = WorkoutSession(
            id = "fixed-id",
            timestamp = 999L,
            targetDurationSeconds = 60,
            soundType = SoundType.INTENSE,
            completed = true,
        )
        val incomplete = base.copy(completed = false)

        assertThat(base).isNotEqualTo(incomplete)
    }

    @Test
    fun `copy produces updated targetDurationSeconds`() {
        val original = WorkoutSession(
            id = "fixed-id",
            timestamp = 999L,
            targetDurationSeconds = 60,
            soundType = SoundType.INTENSE,
            completed = false,
        )
        val longer = original.copy(targetDurationSeconds = 300)

        assertThat(longer.targetDurationSeconds).isEqualTo(300)
        assertThat(longer.id).isEqualTo(original.id)
    }

    @Test
    fun `toString contains key fields`() {
        val session = WorkoutSession(
            id = "test-id-abc",
            timestamp = 12345L,
            targetDurationSeconds = 60,
            soundType = SoundType.INTENSE,
            completed = true,
        )
        val str = session.toString()

        assertThat(str).contains("test-id-abc")
        assertThat(str).contains("60")
        assertThat(str).contains("true")
    }

    @Test
    fun `session accepts all SoundType values`() {
        for (soundType in SoundType.entries) {
            val session = WorkoutSession(
                targetDurationSeconds = 30,
                soundType = soundType,
                completed = true,
            )
            assertThat(session.soundType).isEqualTo(soundType)
        }
    }

    @Test
    fun `session accepts boundary duration of one second`() {
        val session = WorkoutSession(
            targetDurationSeconds = 1,
            soundType = SoundType.INTENSE,
            completed = true,
        )

        assertThat(session.targetDurationSeconds).isEqualTo(1)
    }

    @Test
    fun `session accepts large duration value`() {
        val session = WorkoutSession(
            targetDurationSeconds = 3600,
            soundType = SoundType.GENTLE,
            completed = true,
        )

        assertThat(session.targetDurationSeconds).isEqualTo(3600)
    }
}
