package com.iganapolsky.randomtimer.service

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.VoiceGender
import org.junit.Test

class TimerForegroundServiceStartExtrasTest {
    @Test
    fun `timerConfigFromStartExtras preserves female voice gender`() {
        val config =
            timerConfigFromStartExtras(
                minSeconds = 20,
                maxSeconds = 45,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = "INTENSE",
                volume = 0.5f,
                vibrationEnabled = false,
                useExtendedRange = false,
                voiceEnabled = true,
                voiceGender = "FEMALE",
                repeatRounds = 0,
            )

        assertThat(config.voiceGender).isEqualTo(VoiceGender.FEMALE)
    }

    @Test
    fun `timerConfigFromStartExtras falls back on invalid enum values`() {
        val config =
            timerConfigFromStartExtras(
                minSeconds = 20,
                maxSeconds = 45,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = "NOT_REAL",
                volume = 0.5f,
                vibrationEnabled = false,
                useExtendedRange = false,
                voiceEnabled = true,
                voiceGender = "NOT_REAL",
                repeatRounds = 0,
            )

        assertThat(config.soundType).isEqualTo(SoundType.INTENSE)
        assertThat(config.voiceGender).isEqualTo(VoiceGender.MALE)
    }
}
