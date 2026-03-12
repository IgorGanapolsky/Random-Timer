package com.iganapolsky.randomtimer.service

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.R
import org.junit.Test

class AIVoiceCalloutManagerCueMappingTest {
    @Test
    fun `every elapsed cue used by runtime has bundled audio`() {
        val allElapsedCueResIds = ELAPSED_VOICE_CUES_BY_SECOND.values.map(::voiceResIdForText)

        assertThat(allElapsedCueResIds).doesNotContain(null)
        assertThat(voiceResIdForText(PREVIEW_ELAPSED_CUE)).isNotNull()
    }

    @Test
    fun `preview command cue has bundled audio`() {
        assertThat(voiceResIdForText(PREVIEW_COMMAND_CUE)).isEqualTo(R.raw.cmd_stay_sharp)
    }

    @Test
    fun `runtime callouts are elapsed milestones only`() {
        assertThat(runtimeVoiceCueForElapsedSecond(elapsedSeconds = 18, lastElapsedMilestone = 0)).isNull()
        assertThat(runtimeVoiceCueForElapsedSecond(elapsedSeconds = 30, lastElapsedMilestone = 0))
            .isEqualTo("Thirty seconds.")
        assertThat(runtimeVoiceCueForElapsedSecond(elapsedSeconds = 30, lastElapsedMilestone = 30)).isNull()
    }

    @Test
    fun `unknown cue falls back to bundled drill sergeant clip`() {
        assertThat(voiceResIdOrFallback("Unexpected cue")).isEqualTo(R.raw.cmd_stay_sharp)
        assertThat(voiceResIdForText(DEFAULT_VOICE_FALLBACK_CUE)).isEqualTo(R.raw.cmd_stay_sharp)
    }
}
