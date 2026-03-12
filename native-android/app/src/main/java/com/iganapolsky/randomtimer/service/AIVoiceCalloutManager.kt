package com.iganapolsky.randomtimer.service

import android.content.Context
import android.speech.tts.TextToSpeech
import android.util.Log
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.random.Random

@Singleton
class AIVoiceCalloutManager
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
    ) : TextToSpeech.OnInitListener {
        private var tts: TextToSpeech? = null
        private var isReady = false
        private var lastChaosCueTime = 0
        private var nextChaosCueAt = 0

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
            lastChaosCueTime = 0
            nextChaosCueAt = 0
        }

        fun triggerCallout(remainingSeconds: Int) {
            // Fixed countdown callouts
            val countdownCallouts =
                mapOf(
                    30 to "Thirty seconds remaining. Hold your position.",
                    10 to "Ten seconds. Prepare for impact.",
                    5 to "Five. Four. Three. Two. One.",
                )

            countdownCallouts[remainingSeconds]?.let {
                speak(it)
                return
            }

            // Chaos Drill: randomized tactical cues at unpredictable intervals
            if (remainingSeconds > 30 && shouldFireChaosCue(remainingSeconds)) {
                speak(randomChaosCue())
                lastChaosCueTime = remainingSeconds
                nextChaosCueAt = remainingSeconds - Random.nextInt(8, 20)
            }
        }

        private fun shouldFireChaosCue(remainingSeconds: Int): Boolean {
            if (nextChaosCueAt == 0) {
                // First cue: fire within first 5-15 seconds of the timer running
                nextChaosCueAt = remainingSeconds - Random.nextInt(5, 16)
            }
            return remainingSeconds <= nextChaosCueAt
        }

        private fun randomChaosCue(): String {
            val cues =
                listOf(
                    "Switch stance!",
                    "Move! Move! Move!",
                    "Breathe. Reset.",
                    "Double up!",
                    "Change levels!",
                    "Check your six!",
                    "Pick up the pace!",
                    "Stay sharp!",
                    "Dig deeper!",
                    "Eyes up!",
                    "Recover now!",
                    "Explode!",
                    "Control the center!",
                    "Tighten up!",
                    "Push through it!",
                )
            return cues[Random.nextInt(cues.size)]
        }

        fun shutdown() {
            tts?.stop()
            tts?.shutdown()
        }
    }
