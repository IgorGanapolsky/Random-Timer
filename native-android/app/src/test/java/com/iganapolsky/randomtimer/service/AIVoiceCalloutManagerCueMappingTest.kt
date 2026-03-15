package com.iganapolsky.randomtimer.service

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.R
import org.junit.Test

class AIVoiceCalloutManagerCueMappingTest {
    @Test
    fun `runtime cue uses command phrase at elapsed milestone`() {
        assertThat(runtimeVoiceCueForElapsedSecond(60, lastElapsedMilestone = 0)).isEqualTo("Move now.")
    }

    @Test
    fun `runtime cue is suppressed for duplicate elapsed milestone`() {
        assertThat(runtimeVoiceCueForElapsedSecond(120, lastElapsedMilestone = 120)).isNull()
    }

    @Test
    fun `runtime command cue maps to bundled command asset`() {
        assertThat(voiceResIdForText("Drive forward.")).isEqualTo(R.raw.cmd_drive_forward)
    }

    @Test
    fun `unknown cue falls back to default bundled command asset`() {
        assertThat(voiceResIdOrFallback("Unexpected cue")).isEqualTo(R.raw.cmd_stay_sharp)
    }
}
