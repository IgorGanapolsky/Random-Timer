package com.iganapolsky.randomtimer.domain.model

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class TimerPresetTest {

    @Test
    fun `default values are applied when optional fields omitted`() {
        val preset = TimerPreset(
            id = "test",
            name = "Test Preset",
            emoji = "⏱",
            minSeconds = 30,
            maxSeconds = 90,
        )

        assertThat(preset.soundType).isEqualTo(SoundType.INTENSE)
        assertThat(preset.alarmDuration).isEqualTo(10)
        assertThat(preset.isPro).isFalse()
    }

    @Test
    fun `data class equality holds for identical presets`() {
        val a = TimerPreset(
            id = "boxing",
            name = "Boxing",
            emoji = "🥊",
            minSeconds = 120,
            maxSeconds = 180,
            soundType = SoundType.INTENSE,
            alarmDuration = 10,
            isPro = true,
        )
        val b = TimerPreset(
            id = "boxing",
            name = "Boxing",
            emoji = "🥊",
            minSeconds = 120,
            maxSeconds = 180,
            soundType = SoundType.INTENSE,
            alarmDuration = 10,
            isPro = true,
        )

        assertThat(a).isEqualTo(b)
        assertThat(a.hashCode()).isEqualTo(b.hashCode())
    }

    @Test
    fun `data class inequality when id differs`() {
        val a = TimerPreset(
            id = "preset_a",
            name = "Preset",
            emoji = "⏱",
            minSeconds = 30,
            maxSeconds = 60,
        )
        val b = a.copy(id = "preset_b")

        assertThat(a).isNotEqualTo(b)
    }

    @Test
    fun `copy produces distinct instance with updated field`() {
        val original = TimerPreset(
            id = "quick_drill",
            name = "Quick Drill",
            emoji = "⚡",
            minSeconds = 30,
            maxSeconds = 60,
            isPro = false,
        )
        val proVersion = original.copy(isPro = true)

        assertThat(proVersion.isPro).isTrue()
        assertThat(proVersion.id).isEqualTo(original.id)
        assertThat(proVersion).isNotEqualTo(original)
    }

    @Test
    fun `toString contains key fields`() {
        val preset = TimerPreset(
            id = "tabata",
            name = "Tabata",
            emoji = "🔥",
            minSeconds = 10,
            maxSeconds = 20,
            isPro = true,
        )
        val str = preset.toString()

        assertThat(str).contains("tabata")
        assertThat(str).contains("Tabata")
        assertThat(str).contains("10")
        assertThat(str).contains("20")
    }

    @Test
    fun `preset can hold GENTLE sound type`() {
        val preset = TimerPreset(
            id = "endurance",
            name = "Endurance",
            emoji = "🏋️",
            minSeconds = 300,
            maxSeconds = 600,
            soundType = SoundType.GENTLE,
            alarmDuration = 15,
            isPro = true,
        )

        assertThat(preset.soundType).isEqualTo(SoundType.GENTLE)
        assertThat(preset.alarmDuration).isEqualTo(15)
    }

    @Test
    fun `preset accepts boundary alarm duration of 5 seconds`() {
        val preset = TimerPreset(
            id = "hiit",
            name = "HIIT",
            emoji = "🏃",
            minSeconds = 15,
            maxSeconds = 45,
            alarmDuration = 5,
            isPro = true,
        )

        assertThat(preset.alarmDuration).isEqualTo(5)
    }

    @Test
    fun `preset with isPro false is accessible to free users`() {
        val preset = TimerPreset(
            id = "basic_round",
            name = "Basic Round",
            emoji = "⏰",
            minSeconds = 60,
            maxSeconds = 180,
            soundType = SoundType.GENTLE,
            isPro = false,
        )

        assertThat(preset.isPro).isFalse()
    }

    @Test
    fun `minSeconds and maxSeconds are stored accurately`() {
        val preset = TimerPreset(
            id = "mma",
            name = "MMA 5min",
            emoji = "🤼",
            minSeconds = 240,
            maxSeconds = 300,
        )

        assertThat(preset.minSeconds).isEqualTo(240)
        assertThat(preset.maxSeconds).isEqualTo(300)
    }
}
