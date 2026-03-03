package com.iganapolsky.randomtimer.domain.model

import com.google.common.truth.Truth.assertThat
import com.google.common.truth.Truth.assertWithMessage
import org.junit.Test

class PresetLibraryTest {

    @Test
    fun `presets list is not empty`() {
        assertThat(PresetLibrary.presets).isNotEmpty()
    }

    @Test
    fun `all presets have unique ids`() {
        val ids = PresetLibrary.presets.map { it.id }
        assertThat(ids).containsNoDuplicates()
    }

    @Test
    fun `all presets have minSeconds strictly less than maxSeconds`() {
        for (preset in PresetLibrary.presets) {
            assertWithMessage("minSeconds for preset '${preset.id}'")
                .that(preset.minSeconds)
                .isLessThan(preset.maxSeconds)
        }
    }

    @Test
    fun `all presets have positive minSeconds`() {
        for (preset in PresetLibrary.presets) {
            assertWithMessage("minSeconds for preset '${preset.id}'")
                .that(preset.minSeconds)
                .isGreaterThan(0)
        }
    }

    @Test
    fun `all presets have positive alarmDuration`() {
        for (preset in PresetLibrary.presets) {
            assertWithMessage("alarmDuration for preset '${preset.id}'")
                .that(preset.alarmDuration)
                .isGreaterThan(0)
        }
    }

    @Test
    fun `free presets list contains only non-pro presets`() {
        for (preset in PresetLibrary.freePresets) {
            assertWithMessage("isPro for free preset '${preset.id}'")
                .that(preset.isPro)
                .isFalse()
        }
    }

    @Test
    fun `pro presets list contains only pro presets`() {
        for (preset in PresetLibrary.proPresets) {
            assertWithMessage("isPro for pro preset '${preset.id}'")
                .that(preset.isPro)
                .isTrue()
        }
    }

    @Test
    fun `freePresets and proPresets together equal all presets`() {
        val combined = PresetLibrary.freePresets + PresetLibrary.proPresets
        assertThat(combined).containsExactlyElementsIn(PresetLibrary.presets)
    }

    @Test
    fun `freePresets and proPresets are disjoint`() {
        val freeIds = PresetLibrary.freePresets.map { it.id }.toSet()
        val proIds = PresetLibrary.proPresets.map { it.id }.toSet()
        assertThat(freeIds.intersect(proIds)).isEmpty()
    }

    @Test
    fun `quick_drill free preset is present`() {
        val preset = PresetLibrary.presets.find { it.id == "quick_drill" }
        assertThat(preset).isNotNull()
        assertThat(preset!!.isPro).isFalse()
        assertThat(preset.minSeconds).isEqualTo(30)
        assertThat(preset.maxSeconds).isEqualTo(60)
    }

    @Test
    fun `basic_round free preset is present`() {
        val preset = PresetLibrary.presets.find { it.id == "basic_round" }
        assertThat(preset).isNotNull()
        assertThat(preset!!.isPro).isFalse()
        assertThat(preset.soundType).isEqualTo(SoundType.GENTLE)
    }

    @Test
    fun `boxing_3min pro preset is present`() {
        val preset = PresetLibrary.presets.find { it.id == "boxing_3min" }
        assertThat(preset).isNotNull()
        assertThat(preset!!.isPro).isTrue()
        assertThat(preset.minSeconds).isEqualTo(120)
        assertThat(preset.maxSeconds).isEqualTo(180)
    }

    @Test
    fun `tabata pro preset has correct short-interval timing`() {
        val preset = PresetLibrary.presets.find { it.id == "tabata" }
        assertThat(preset).isNotNull()
        assertThat(preset!!.minSeconds).isEqualTo(10)
        assertThat(preset.maxSeconds).isEqualTo(20)
        assertThat(preset.alarmDuration).isEqualTo(5)
        assertThat(preset.isPro).isTrue()
    }

    @Test
    fun `endurance pro preset has correct long-duration timing`() {
        val preset = PresetLibrary.presets.find { it.id == "endurance" }
        assertThat(preset).isNotNull()
        assertThat(preset!!.minSeconds).isEqualTo(300)
        assertThat(preset.maxSeconds).isEqualTo(600)
        assertThat(preset.soundType).isEqualTo(SoundType.GENTLE)
        assertThat(preset.alarmDuration).isEqualTo(15)
    }

    @Test
    fun `findMatchingPreset returns correct preset for exact range match`() {
        val config = TimerConfig(
            minSeconds = 30,
            maxSeconds = 60,
            alarmDuration = 10,
            hiddenMode = false,
            repeatEnabled = false,
            soundType = SoundType.INTENSE,
            volume = 0.5f,
        )

        val result = PresetLibrary.findMatchingPreset(config)

        assertThat(result).isNotNull()
        assertThat(result!!.id).isEqualTo("quick_drill")
    }

    @Test
    fun `findMatchingPreset returns null when no preset matches`() {
        val config = TimerConfig(
            minSeconds = 7,
            maxSeconds = 77,
            alarmDuration = 10,
            hiddenMode = false,
            repeatEnabled = false,
            soundType = SoundType.INTENSE,
            volume = 0.5f,
        )

        val result = PresetLibrary.findMatchingPreset(config)

        assertThat(result).isNull()
    }

    @Test
    fun `findMatchingPreset matches mma_5min preset`() {
        val config = TimerConfig(
            minSeconds = 240,
            maxSeconds = 300,
            alarmDuration = 10,
            hiddenMode = false,
            repeatEnabled = false,
            soundType = SoundType.INTENSE,
            volume = 0.5f,
        )

        val result = PresetLibrary.findMatchingPreset(config)

        assertThat(result).isNotNull()
        assertThat(result!!.id).isEqualTo("mma_5min")
    }

    @Test
    fun `findMatchingPreset only matches by minSeconds and maxSeconds not soundType`() {
        // soundType mismatch should still find the preset (matching is by range only)
        val config = TimerConfig(
            minSeconds = 60,
            maxSeconds = 180,
            alarmDuration = 10,
            hiddenMode = false,
            repeatEnabled = false,
            soundType = SoundType.KLAXON,
            volume = 0.5f,
        )

        val result = PresetLibrary.findMatchingPreset(config)

        assertThat(result).isNotNull()
        assertThat(result!!.id).isEqualTo("basic_round")
    }

    @Test
    fun `at least two free presets exist`() {
        assertThat(PresetLibrary.freePresets.size).isAtLeast(2)
    }

    @Test
    fun `majority of presets are pro`() {
        assertThat(PresetLibrary.proPresets.size)
            .isGreaterThan(PresetLibrary.freePresets.size)
    }

    @Test
    fun `all presets have non-blank names`() {
        for (preset in PresetLibrary.presets) {
            assertWithMessage("name blank for preset '${preset.id}'")
                .that(preset.name.isBlank())
                .isFalse()
        }
    }

    @Test
    fun `all presets have non-blank emoji`() {
        for (preset in PresetLibrary.presets) {
            assertWithMessage("emoji blank for preset '${preset.id}'")
                .that(preset.emoji.isBlank())
                .isFalse()
        }
    }
}
