package com.iganapolsky.randomtimer.appfunctions

import androidx.appfunctions.AppFunctionInvalidArgumentException
import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.EntitlementLevel
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
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
    private val defaultRequest =
        TimerFunctionRequest(
            minSeconds = 15,
            maxSeconds = 45,
            alarmDuration = 10,
            soundType = "INTENSE",
            voiceEnabled = false,
            voiceGender = "MALE",
            hiddenMode = false,
            repeatEnabled = false,
            vibrationEnabled = false,
        )

    @Test
    fun createReturnsValidFreeConfigForFreeSafeOptions() {
        val config = createRequest(defaultRequest.copy(vibrationEnabled = true, hiddenMode = true))

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
    fun createRejectsProSoundForFreeEntitlement() {
        val error = assertInvalidRequest(defaultRequest.copy(soundType = "KLAXON"))

        assertThat(error.message).contains("requires Pro")
    }

    @Test
    fun createRejectsVoiceForFreeEntitlement() {
        val error = assertInvalidRequest(defaultRequest.copy(voiceEnabled = true, voiceGender = "FEMALE"))

        assertThat(error.message).contains("Voice callouts require Pro")
    }

    @Test
    fun createAllowsProOnlyFieldsForEliteEntitlement() {
        val config =
            createRequest(
                defaultRequest.copy(
                    minSeconds = 300,
                    maxSeconds = 450,
                    alarmDuration = 15,
                    soundType = "KLAXON",
                    voiceEnabled = true,
                    voiceGender = "FEMALE",
                    repeatEnabled = true,
                    vibrationEnabled = true,
                ),
                entitlementLevel = EntitlementLevel.ELITE,
            )

        assertThat(config.useExtendedRange).isTrue()
        assertThat(config.soundType).isEqualTo(SoundType.KLAXON)
        assertThat(config.voiceEnabled).isTrue()
        assertThat(config.voiceGender).isEqualTo(VoiceGender.FEMALE)
        assertThat(config.repeatEnabled).isTrue()
    }

    @Test
    fun createRejectsUnsupportedAlarmDuration() {
        val error = assertInvalidRequest(defaultRequest.copy(alarmDuration = 7))

        assertThat(error.message).contains("alarmDuration must be one of")
    }

    @Test
    fun createRejectsExtendedRangeForFreeEntitlement() {
        val error = assertInvalidRequest(defaultRequest.copy(minSeconds = 60, maxSeconds = 400))

        assertThat(error.message).contains("Extended timer ranges")
    }

    @Test
    fun createRejectsUnsupportedSoundType() {
        val error = assertInvalidRequest(defaultRequest.copy(soundType = "LOUD"))

        assertThat(error.message).contains("soundType must be one of")
    }

    @Test
    fun createRejectsUnsupportedVoiceGender() {
        val error = assertInvalidRequest(defaultRequest.copy(voiceGender = "ROBOT"))

        assertThat(error.message).contains("voiceGender must be one of")
    }

    @Test
    fun createWrapsTimerConfigValidationFailuresAsInvalidArguments() {
        val error = assertInvalidRequest(defaultRequest.copy(minSeconds = 60, maxSeconds = 45))

        assertThat(error.message).contains("Maximum seconds must be >= minimum seconds")
    }

    private fun createRequest(
        request: TimerFunctionRequest = defaultRequest,
        entitlementLevel: EntitlementLevel = EntitlementLevel.NONE,
    ): TimerConfig =
        factory.create(
            request = request,
            entitlementLevel = entitlementLevel,
        )

    private fun assertInvalidRequest(
        request: TimerFunctionRequest = defaultRequest,
        entitlementLevel: EntitlementLevel = EntitlementLevel.NONE,
    ): AppFunctionInvalidArgumentException =
        assertThrows(AppFunctionInvalidArgumentException::class.java) {
            createRequest(request = request, entitlementLevel = entitlementLevel)
        }
}
