package com.iganapolsky.randomtimer.service

import android.content.Context
import android.speech.tts.TextToSpeech
import android.util.Log
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.random.Random

internal data class VoiceCandidate(
    val name: String,
    val locale: Locale,
)

internal fun selectPreferredVoice(candidates: List<VoiceCandidate>): VoiceCandidate? =
    candidates
        .filter { candidate -> candidate.locale.language.equals(Locale.US.language, ignoreCase = true) }
        .firstOrNull { candidate ->
            AIVoiceCalloutManager.preferredVoiceNames.any { preferred ->
                candidate.name.contains(preferred, ignoreCase = true)
            }
        }

@Singleton
class AIVoiceCalloutManager
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
    ) : TextToSpeech.OnInitListener {
        private var tts: TextToSpeech? = null
        private var isReady = false
        private var lastElapsedMilestone = 0
        private var nextCommandCueAt = 0
        private var lastCommandCueAt = 0

        companion object {
            val preferredVoiceNames = listOf("en-us-x-tpf", "en-us-x-sfg", "en-US-language")
        }

        init {
            tts = TextToSpeech(context, this)
        }

        override fun onInit(status: Int) {
            if (status == TextToSpeech.SUCCESS) {
                val result = tts?.setLanguage(Locale.US)
                if (result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED) {
                    isReady = true
                    Log.d("AIVoiceCallout", "TTS Ready")
                }
            }
        }

        fun speak(text: String) {
            if (isReady) {
                Log.d("AIVoiceCallout", "Speaking: $text")
                tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, null)
            }
        }

        fun resetSession() {
            lastElapsedMilestone = 0
            nextCommandCueAt = 0
            lastCommandCueAt = 0
        }

        fun preview() {
            previewCommandCue()
        }

        fun previewCommandCue() {
            speak(randomCommandCue())
        }

        fun previewCountdownCue() {
            // With elapsed model, preview an elapsed milestone announcement
            speak("Thirty seconds. Stay locked in.")
        }

        // Called every second with elapsed seconds since timer started.
        fun triggerCallout(elapsedSeconds: Int) {
            // Elapsed milestone callouts — fire once per milestone
            elapsedMilestone(elapsedSeconds)?.let {
                speak(it)
                lastElapsedMilestone = elapsedSeconds
                return
            }

            // Random command cues fire throughout the session
            if (shouldFireCommandCue(elapsedSeconds)) {
                speak(randomCommandCue())
                lastCommandCueAt = elapsedSeconds
                nextCommandCueAt = elapsedSeconds + Random.nextInt(12, 26)
            }
        }

        private fun elapsedMilestone(elapsed: Int): String? {
            if (elapsed == lastElapsedMilestone) return null
            return when (elapsed) {
                30  -> "Thirty seconds."
                60  -> "One minute. Keep moving."
                90  -> "One minute thirty."
                120 -> "Two minutes. Stay locked in."
                180 -> "Three minutes. Drive forward."
                240 -> "Four minutes. Hold the line."
                300 -> "Five minutes. Finish strong."
                360 -> "Six minutes."
                420 -> "Seven minutes."
                480 -> "Eight minutes."
                540 -> "Nine minutes."
                600 -> "Ten minutes. Outstanding."
                else -> null
            }
        }

        private fun shouldFireCommandCue(elapsedSeconds: Int): Boolean {
            if (nextCommandCueAt == 0) {
                nextCommandCueAt = Random.nextInt(8, 21)
            }
            return elapsedSeconds >= nextCommandCueAt
        }

        private fun randomCommandCue(): String {
            val cues = listOf(
                "Move now.",
                "Stay sharp.",
                "Eyes front.",
                "Hands up.",
                "Reset. Breathe.",
                "Push the pace.",
                "Explode.",
                "Recover. Then go.",
                "Hold the line.",
                "Drive forward.",
                "Keep pressure.",
                "Lock in.",
                "Finish strong.",
                "Breathe and move.",
                "Switch stance.",
                "Double up.",
                "Check your six.",
                "Dig deeper.",
                "Tighten up.",
                "Push through it.",
            )
            return cues[Random.nextInt(cues.size)]
        }

        fun shutdown() {
            tts?.stop()
            tts?.shutdown()
        }
    }
