package com.iganapolsky.randomtimer.domain.model

import com.google.common.truth.Truth.assertThat
import org.junit.Test
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

class TimerConfigTest {
    @Test
    fun `default config has valid range`() {
        val config = TimerConfig.DEFAULT

        assertThat(config.minSeconds).isEqualTo(0)
        assertThat(config.maxSeconds).isEqualTo(300)
        assertThat(config.volume).isEqualTo(0.5f)
        assertThat(config.vibrationEnabled).isFalse()
        assertThat(config.voiceEnabled).isFalse()
    }

    @Test
    fun `default config has loop OFF`() {
        val config = TimerConfig.DEFAULT

        assertThat(config.repeatEnabled).isFalse()
    }

    @Test
    fun `config accepts valid range`() {
        val config =
            TimerConfig(
                minSeconds = 60,
                maxSeconds = 300,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                vibrationEnabled = false,
            )

        assertThat(config.minDuration).isEqualTo(1.minutes)
        assertThat(config.maxDuration).isEqualTo(5.minutes)
    }

    @Test
    fun `config accepts same min and max`() {
        val config =
            TimerConfig(
                minSeconds = 120,
                maxSeconds = 120,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                vibrationEnabled = false,
            )

        assertThat(config.minSeconds).isEqualTo(config.maxSeconds)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `config rejects negative duration`() {
        TimerConfig(
            minSeconds = -1,
            maxSeconds = 300,
            alarmDuration = 10,
            hiddenMode = false,
            repeatEnabled = false,
            soundType = SoundType.INTENSE,
            volume = 0.5f,
            vibrationEnabled = false,
        )
    }

    @Test(expected = IllegalArgumentException::class)
    fun `config rejects max less than min`() {
        TimerConfig(
            minSeconds = 360,
            maxSeconds = 300,
            alarmDuration = 10,
            hiddenMode = false,
            repeatEnabled = false,
            soundType = SoundType.INTENSE,
            volume = 0.5f,
            vibrationEnabled = false,
        )
    }

    @Test(expected = IllegalArgumentException::class)
    fun `config rejects duration over 60 minutes`() {
        TimerConfig(
            minSeconds = 60,
            maxSeconds = 3601, // exceeds 60 min pro max
            alarmDuration = 10,
            hiddenMode = false,
            repeatEnabled = false,
            soundType = SoundType.INTENSE,
            volume = 0.5f,
            vibrationEnabled = false,
        )
    }

    @Test
    fun `config accepts pro range up to 60 minutes`() {
        val config =
            TimerConfig(
                minSeconds = 60,
                maxSeconds = 3600, // 60 minutes - pro max
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                vibrationEnabled = false,
                useExtendedRange = true,
            )
        assertThat(config.maxSeconds).isEqualTo(3600)
    }

    @Test
    fun `config can enable vibration`() {
        val config =
            TimerConfig(
                minSeconds = 30,
                maxSeconds = 120,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                vibrationEnabled = true,
            )

        assertThat(config.vibrationEnabled).isTrue()
    }

    @Test
    fun `config can enable voice callouts`() {
        val config =
            TimerConfig(
                minSeconds = 30,
                maxSeconds = 120,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                vibrationEnabled = false,
                voiceEnabled = true,
            )

        assertThat(config.voiceEnabled).isTrue()
    }

    @Test
    fun `default alarm duration is 10 seconds`() {
        val config = TimerConfig.DEFAULT

        assertThat(config.alarmDuration).isEqualTo(10)
    }

    @Test
    fun `toggle extended range restores last free range`() {
        val current =
            TimerConfig(
                minSeconds = 900,
                maxSeconds = 1800,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                vibrationEnabled = false,
                useExtendedRange = true,
            )
        val profiles =
            RangeToggleProfiles(
                freeMinSeconds = 30,
                freeMaxSeconds = 120,
                extendedMinSeconds = 900,
                extendedMaxSeconds = 1800,
            )

        val result = toggleExtendedRange(current, profiles)

        assertThat(result.config.useExtendedRange).isFalse()
        assertThat(result.config.minSeconds).isEqualTo(30)
        assertThat(result.config.maxSeconds).isEqualTo(120)
        assertThat(result.profiles.extendedMinSeconds).isEqualTo(900)
        assertThat(result.profiles.extendedMaxSeconds).isEqualTo(1800)
    }

    @Test
    fun `toggle extended range restores last extended range`() {
        val current =
            TimerConfig(
                minSeconds = 45,
                maxSeconds = 180,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                vibrationEnabled = false,
                useExtendedRange = false,
            )
        val profiles =
            RangeToggleProfiles(
                freeMinSeconds = 45,
                freeMaxSeconds = 180,
                extendedMinSeconds = 1200,
                extendedMaxSeconds = 2400,
            )

        val result = toggleExtendedRange(current, profiles)

        assertThat(result.config.useExtendedRange).isTrue()
        assertThat(result.config.minSeconds).isEqualTo(1200)
        assertThat(result.config.maxSeconds).isEqualTo(2400)
        assertThat(result.profiles.freeMinSeconds).isEqualTo(45)
        assertThat(result.profiles.freeMaxSeconds).isEqualTo(180)
    }
}
