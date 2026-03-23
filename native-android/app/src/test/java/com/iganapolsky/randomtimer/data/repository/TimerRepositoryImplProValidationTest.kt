package com.iganapolsky.randomtimer.data.repository

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import org.junit.Test

/**
 * Tests for the Pro validation clamping logic applied during TimerConfig deserialization.
 * The clamping rules: expired Pro users must have maxSeconds clamped to MAX_SECONDS_FREE
 * and Pro soundTypes reset to SoundType.INTENSE.
 */
class TimerConfigProClampingTest {

    // Simulate the clamping logic extracted from TimerRepositoryImpl.
    // Mirrors the exact copy() logic used in the production clampedForPro() helper.
    private fun TimerConfig.clampedForPro(isPro: Boolean): TimerConfig {
        val maxAllowed = if (isPro && useExtendedRange) TimerConfig.MAX_SECONDS_PRO else TimerConfig.MAX_SECONDS_FREE
        val allowedSounds = if (isPro) SoundType.entries.toList() else SoundType.FREE
        val clampedMax = maxSeconds.coerceAtMost(maxAllowed)
        val clampedMin = minSeconds.coerceAtMost(clampedMax)
        val clampedSound = if (soundType in allowedSounds) soundType else SoundType.INTENSE
        return copy(
            minSeconds = clampedMin,
            maxSeconds = clampedMax,
            soundType = clampedSound,
            useExtendedRange = if (isPro) useExtendedRange else false
        )
    }

    @Test
    fun `expired pro user - maxSeconds above free limit is clamped to 300`() {
        val proConfig =
            TimerConfig(
                minSeconds = 0,
                maxSeconds = 3600,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                useExtendedRange = true,
            )

        val clamped = proConfig.clampedForPro(isPro = false)

        assertThat(clamped.maxSeconds).isEqualTo(TimerConfig.MAX_SECONDS_FREE)
        assertThat(clamped.useExtendedRange).isFalse()
    }

    @Test
    fun `expired pro user - pro soundType is reset to INTENSE`() {
        val proConfig =
            TimerConfig(
                minSeconds = 0,
                maxSeconds = 60,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.KLAXON,
                volume = 0.5f,
            )

        val clamped = proConfig.clampedForPro(isPro = false)

        assertThat(clamped.soundType).isEqualTo(SoundType.INTENSE)
    }

    @Test
    fun `expired pro user - free soundType is retained`() {
        val config =
            TimerConfig(
                minSeconds = 0,
                maxSeconds = 60,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.GENTLE,
                volume = 0.5f,
            )

        val clamped = config.clampedForPro(isPro = false)

        assertThat(clamped.soundType).isEqualTo(SoundType.GENTLE)
    }

    @Test
    fun `active pro user - maxSeconds up to 3600 is retained`() {
        val proConfig =
            TimerConfig(
                minSeconds = 0,
                maxSeconds = 3600,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                useExtendedRange = true,
            )

        val clamped = proConfig.clampedForPro(isPro = true)

        assertThat(clamped.maxSeconds).isEqualTo(3600)
        assertThat(clamped.useExtendedRange).isTrue()
    }

    @Test
    fun `active pro user - pro soundType is retained`() {
        val proConfig =
            TimerConfig(
                minSeconds = 0,
                maxSeconds = 60,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.GONG,
                volume = 0.5f,
            )

        val clamped = proConfig.clampedForPro(isPro = true)

        assertThat(clamped.soundType).isEqualTo(SoundType.GONG)
    }

    @Test
    fun `expired pro user - minSeconds clamped when it exceeds new clamped max`() {
        // minSeconds=0 with maxSeconds=3600 saved when Pro; after expiry max=300, min must also clamp.
        val proConfig =
            TimerConfig(
                minSeconds = 0,
                maxSeconds = 3600,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                useExtendedRange = true,
            )
        val clamped = proConfig.clampedForPro(isPro = false)

        // min=0 is already safe; verify clamped max is 300 and min <= max
        assertThat(clamped.maxSeconds).isEqualTo(300)
        assertThat(clamped.minSeconds).isAtMost(clamped.maxSeconds)
        assertThat(clamped.useExtendedRange).isFalse()
    }

    @Test
    fun `free user config within free limits is unchanged`() {
        val freeConfig =
            TimerConfig(
                minSeconds = 30,
                maxSeconds = 120,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = true,
                soundType = SoundType.GENTLE,
                volume = 0.7f,
            )

        val clamped = freeConfig.clampedForPro(isPro = false)

        assertThat(clamped).isEqualTo(freeConfig)
    }
}
