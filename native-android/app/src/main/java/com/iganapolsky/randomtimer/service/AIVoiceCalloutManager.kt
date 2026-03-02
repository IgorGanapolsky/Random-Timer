package com.iganapolsky.randomtimer.service

import android.content.Context
import android.speech.tts.TextToSpeech
import android.util.Log
import com.iganapolsky.randomtimer.domain.model.EliteConfig
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Handles AI-driven voice callouts for the "Elite Tactical" tier.
 * Cues are randomized based on training focus (Combat, Shooting, etc.)
 */
@Singleton
class AIVoiceCalloutManager @Inject constructor(
    @ApplicationContext private val context: Context
) : TextToSpeech.OnInitListener {

    private var tts: TextToSpeech? = null
    private var isInitialized = false
    
    private val combatCues = listOf("Jab", "Cross", "Hook", "Sprawl", "Move", "Double up", "Circle left", "Circle right")
    private val shootingCues = listOf("Reload", "Transition", "Move", "Low port", "Scan", "Safety on")
    
    init {
        tts = TextToSpeech(context, this)
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            val result = tts?.setLanguage(Locale.US)
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                Log.e("AICallout", "TTS Language not supported")
            } else {
                isInitialized = true
            }
        }
    }

    fun speakRandomCue(focus: TrainingFocus = TrainingFocus.COMBAT) {
        if (!isInitialized) return
        
        val cues = when (focus) {
            TrainingFocus.COMBAT -> combatCues
            TrainingFocus.SHOOTING -> shootingCues
        }
        
        val cue = cues.random()
        tts?.speak(cue, TextToSpeech.QUEUE_FLUSH, null, "cue_$cue")
    }

    fun shutdown() {
        tts?.stop()
        tts?.shutdown()
    }
}

enum class TrainingFocus {
    COMBAT, SHOOTING
}
