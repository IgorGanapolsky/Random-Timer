package com.iganapolsky.randomtimer.service

import com.google.common.truth.Truth.assertThat
import org.junit.Test
import java.util.Locale

class AIVoiceCalloutManagerSelectionTest {

    @Test
    fun `selectPreferredVoice ignores non english male voices`() {
        val selected = selectPreferredVoice(
            listOf(
                VoiceCandidate("hi-IN-x-cfn#male_3-local", Locale("hi", "IN")),
                VoiceCandidate("en-us-x-sfg#male_1-local", Locale.US),
            ),
        )

        assertThat(selected?.name).isEqualTo("en-us-x-sfg#male_1-local")
    }

    @Test
    fun `selectPreferredVoice returns null when only non english voices are available`() {
        val selected = selectPreferredVoice(
            listOf(
                VoiceCandidate("hi-IN-x-cfn#male_3-local", Locale("hi", "IN")),
                VoiceCandidate("es-es-x-eef-local", Locale("es", "ES")),
            ),
        )

        assertThat(selected).isNull()
    }
}
