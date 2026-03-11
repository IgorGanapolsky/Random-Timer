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
        companion object {
            private const val TACTICAL_PITCH = 0.72f
            private const val TACTICAL_RATE = 0.82f
            internal val preferredVoiceNames =
                listOf("male", "en-us-x-sfg#male_1-local", "en-us-x-sfg", "en-us-x-iol-local", "en-us-language")
        }

        private var tts: TextToSpeech? = null
        private var isReady = false
        private var lastCommandCueTime = 0
        private var nextCommandCueAt = 0

        init {
            tts = TextToSpeech(context, this)
        }

        override fun onInit(status: Int) {
            if (status == TextToSpeech.SUCCESS) {
                val result = tts?.setLanguage(Locale.US)
                if (result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED) {
                    tts?.setPitch(TACTICAL_PITCH)
                    tts?.setSpeechRate(TACTICAL_RATE)
                    val preferredVoice =
                        selectPreferredVoice(
                            tts
                                ?.voices
                                ?.mapNotNull { voice ->
                                    val locale = voice.locale ?: return@mapNotNull null
                                    VoiceCandidate(name = voice.name, locale = locale)
                                }.orEmpty(),
                        )?.let { selected ->
                            tts?.voices?.firstOrNull { voice ->
                                voice.name == selected.name &&
                                    voice.locale?.toLanguageTag() == selected.locale.toLanguageTag()
                            }
                        }
                    if (preferredVoice != null) {
                        tts?.voice = preferredVoice
                    }
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
            lastCommandCueTime = 0
            nextCommandCueAt = 0
        }

        fun previewCountdownCue() {
            val previewCues =
                listOf(
                    "Thirty seconds. Stay ready.",
                    "Ten seconds. Stand by.",
                    "Five. Four. Three. Two. One.",
                )
            speak(previewCues[Random.nextInt(previewCues.size)])
        }

        fun previewCommandCue() {
            speak(randomCommandCue())
        }

        fun triggerCallout(remainingSeconds: Int) {
            // Fixed countdown callouts
            val countdownCallouts =
                mapOf(
                    30 to "Thirty seconds. Stay ready.",
                    10 to "Ten seconds. Stand by.",
                    5 to "Five. Four. Three. Two. One.",
                )

            countdownCallouts[remainingSeconds]?.let {
                speak(it)
                return
            }

            // Randomized command cues break predictability during longer timers.
            if (remainingSeconds > 30 && shouldFireCommandCue(remainingSeconds)) {
                speak(randomCommandCue())
                lastCommandCueTime = remainingSeconds
                nextCommandCueAt = remainingSeconds - Random.nextInt(8, 20)
            }
        }

        private fun shouldFireCommandCue(remainingSeconds: Int): Boolean {
            if (nextCommandCueAt == 0) {
                // First cue: fire within first 5-15 seconds of the timer running
                nextCommandCueAt = remainingSeconds - Random.nextInt(5, 16)
            }
            return remainingSeconds <= nextCommandCueAt
        }

        private fun randomCommandCue(): String {
            val cues =
                listOf(
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
                    "Stand by.",
                    "Lock in.",
                    "Finish strong.",
                    "Breathe and move.",
                )
            return cues[Random.nextInt(cues.size)]
        }

        fun shutdown() {
            tts?.stop()
            tts?.shutdown()
        }
    }
