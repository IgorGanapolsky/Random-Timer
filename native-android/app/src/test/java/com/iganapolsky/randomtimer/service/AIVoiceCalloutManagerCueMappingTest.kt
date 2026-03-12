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
    fun `every command cue used by runtime has bundled audio`() {
        val allCommandCueResIds = COMMAND_VOICE_CUES.map(::voiceResIdForText)

        assertThat(allCommandCueResIds).doesNotContain(null)
    }

    @Test
    fun `runtime command cues stay neutral and non prescriptive`() {
        assertThat(COMMAND_VOICE_CUES)
            .containsExactly(
                "Stay sharp.",
                "Reset. Breathe.",
            ).inOrder()
    }

    @Test
    fun `unknown cue falls back to bundled drill sergeant clip`() {
        assertThat(voiceResIdOrFallback("Unexpected cue")).isEqualTo(R.raw.cmd_stay_sharp)
        assertThat(voiceResIdForText(DEFAULT_VOICE_FALLBACK_CUE)).isEqualTo(R.raw.cmd_stay_sharp)
    }
}
