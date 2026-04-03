package com.iganapolsky.randomtimer.appfunctions

import androidx.appfunctions.AppFunctionInvalidArgumentException
import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.EntitlementLevel
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.VoiceGender
import org.junit.Assert.assertThrows
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class RandomTimerAppFunctionConfigFactoryTest {
    private val factory = RandomTimerAppFunctionConfigFactory()

    @Test
    fun `create returns valid free config for free-safe options`() {
        val config =
            factory.create(
                minSeconds = 15,
                maxSeconds = 45,
                alarmDuration = 10,
                soundType = "INTENSE",
                voiceEnabled = false,
                voiceGender = "MALE",
                hiddenMode = true,
                repeatEnabled = false,
                vibrationEnabled = true,
                entitlementLevel = EntitlementLevel.NONE,
            )

        assertThat(config.minSeconds).isEqualTo(15)
        assertThat(config.maxSeconds).isEqualTo(45)
        assertThat(config.soundType).isEqualTo(SoundType.INTENSE)
        assertThat(config.voiceEnabled).isFalse()
        assertThat(config.voiceGender).isEqualTo(VoiceGender.MALE)
        assertThat(config.useExtendedRange).isFalse()
        assertThat(config.hiddenMode).isTrue()
        assertThat(config.vibrationEnabled).isTrue()
    }

    @Test
    fun `create rejects pro sound for free entitlement`() {
        val error =
            assertThrows(AppFunctionInvalidArgumentException::class.java) {
                factory.create(
                    minSeconds = 15,
                    maxSeconds = 45,
                    alarmDuration = 10,
                    soundType = "KLAXON",
                    voiceEnabled = false,
                    voiceGender = "MALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                    entitlementLevel = EntitlementLevel.NONE,
                )
            }

        assertThat(error.message).contains("requires Pro")
    }

    @Test
    fun `create rejects voice for free entitlement`() {
        val error =
            assertThrows(AppFunctionInvalidArgumentException::class.java) {
                factory.create(
                    minSeconds = 15,
                    maxSeconds = 45,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = true,
                    voiceGender = "FEMALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                    entitlementLevel = EntitlementLevel.NONE,
                )
            }

        assertThat(error.message).contains("Voice callouts require Pro")
    }

    @Test
    fun `create allows pro-only fields for elite entitlement`() {
        val config =
            factory.create(
                minSeconds = 300,
                maxSeconds = 450,
                alarmDuration = 15,
                soundType = "KLAXON",
                voiceEnabled = true,
                voiceGender = "FEMALE",
                hiddenMode = false,
                repeatEnabled = true,
                vibrationEnabled = true,
                entitlementLevel = EntitlementLevel.ELITE,
            )

        assertThat(config.useExtendedRange).isTrue()
        assertThat(config.soundType).isEqualTo(SoundType.KLAXON)
        assertThat(config.voiceEnabled).isTrue()
        assertThat(config.voiceGender).isEqualTo(VoiceGender.FEMALE)
        assertThat(config.repeatEnabled).isTrue()
    }

    @Test
    fun `create rejects unsupported alarm duration`() {
        val error =
            assertThrows(AppFunctionInvalidArgumentException::class.java) {
                factory.create(
                    minSeconds = 15,
                    maxSeconds = 45,
                    alarmDuration = 7,
                    soundType = "INTENSE",
                    voiceEnabled = false,
                    voiceGender = "MALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                    entitlementLevel = EntitlementLevel.NONE,
                )
            }

        assertThat(error.message).contains("alarmDuration must be one of")
    }

    @Test
    fun `create rejects extended range for free entitlement`() {
        val error =
            assertThrows(AppFunctionInvalidArgumentException::class.java) {
                factory.create(
                    minSeconds = 60,
                    maxSeconds = 400,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = false,
                    voiceGender = "MALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                    entitlementLevel = EntitlementLevel.NONE,
                )
            }

        assertThat(error.message).contains("Extended timer ranges")
    }

    @Test
    fun `create rejects unsupported sound type`() {
        val error =
            assertThrows(AppFunctionInvalidArgumentException::class.java) {
                factory.create(
                    minSeconds = 15,
                    maxSeconds = 45,
                    alarmDuration = 10,
                    soundType = "LOUD",
                    voiceEnabled = false,
                    voiceGender = "MALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                    entitlementLevel = EntitlementLevel.NONE,
                )
            }

        assertThat(error.message).contains("soundType must be one of")
    }

    @Test
    fun `create rejects unsupported voice gender`() {
        val error =
            assertThrows(AppFunctionInvalidArgumentException::class.java) {
                factory.create(
                    minSeconds = 15,
                    maxSeconds = 45,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = false,
                    voiceGender = "ROBOT",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                    entitlementLevel = EntitlementLevel.NONE,
                )
            }

        assertThat(error.message).contains("voiceGender must be one of")
    }

    @Test
    fun `create wraps timer config validation failures as invalid arguments`() {
        val error =
            assertThrows(AppFunctionInvalidArgumentException::class.java) {
                factory.create(
                    minSeconds = 60,
                    maxSeconds = 45,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = false,
                    voiceGender = "MALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                    entitlementLevel = EntitlementLevel.NONE,
                )
            }

        assertThat(error.message).contains("Maximum seconds must be >= minimum seconds")
    }
}
