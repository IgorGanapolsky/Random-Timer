package com.iganapolsky.randomtimer.service

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.util.Log
import com.iganapolsky.randomtimer.R
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

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

internal const val PREVIEW_ELAPSED_CUE = "Thirty seconds. Stay locked in."
internal const val PREVIEW_COMMAND_CUE = "Stay sharp."

internal val COMMAND_VOICE_CUES =
    listOf(
        "Stay sharp.",
        "Push through.",
        "Move now!",
        "Drive forward.",
        "Keep the pressure.",
        "Push the pace.",
        "Reset and breathe.",
    )

internal val ELAPSED_VOICE_CUES_BY_SECOND =
    mapOf(
        30 to "Thirty seconds.",
        60 to "One minute. Keep moving.",
        90 to "One minute thirty.",
        120 to "Two minutes. Stay locked in.",
        180 to "Three minutes. Drive forward.",
        300 to "Five minutes. Finish strong.",
        600 to "Ten minutes. Outstanding.",
    )

internal const val DEFAULT_VOICE_FALLBACK_CUE = PREVIEW_COMMAND_CUE

internal fun runtimeVoiceCueForElapsedSecond(
    elapsedSeconds: Int,
    lastElapsedMilestone: Int,
): String? {
    if (elapsedSeconds == lastElapsedMilestone) return null
    return ELAPSED_VOICE_CUES_BY_SECOND[elapsedSeconds]
}

internal fun voiceResIdForText(text: String): Int? =
    when (text) {
        "Thirty seconds." -> R.raw.elapsed_30s
        "One minute. Keep moving." -> R.raw.elapsed_60s
        "One minute thirty." -> R.raw.elapsed_90s
        "Two minutes. Stay locked in." -> R.raw.elapsed_120s
        "Three minutes. Drive forward." -> R.raw.elapsed_180s
        "Five minutes. Finish strong." -> R.raw.elapsed_300s
        "Ten minutes. Outstanding." -> R.raw.elapsed_600s
        "Stay sharp." -> R.raw.cmd_stay_sharp
        "Push through." -> R.raw.cmd_push_through
        "Move now!" -> R.raw.cmd_move_now
        "Drive forward." -> R.raw.cmd_drive_forward
        "Keep the pressure." -> R.raw.cmd_keep_pressure
        "Push the pace." -> R.raw.cmd_push_pace
        "Reset and breathe." -> R.raw.cmd_reset_breathe
        PREVIEW_ELAPSED_CUE -> R.raw.preview_elapsed
        PREVIEW_COMMAND_CUE -> R.raw.cmd_stay_sharp
        else -> null
    }

internal fun voiceResIdOrFallback(text: String): Int = voiceResIdForText(text) ?: R.raw.cmd_stay_sharp

@Singleton
class AIVoiceCalloutManager
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
    ) {
        private var lastElapsedMilestone = 0
        private var mediaPlayer: MediaPlayer? = null
        private var currentVolume: Float = 1.0f
        private var previewCycleIndex = 0

        companion object {
            val preferredVoiceNames = listOf("en-us-x-tpf", "en-us-x-sfg", "en-US-language")
        }

        fun setVolume(volume: Float) {
            currentVolume = volume.coerceIn(0f, 1f)
            Log.d("AIVoiceCallout", "setVolume: $currentVolume")
            mediaPlayer?.setVolume(currentVolume, currentVolume)
        }

        fun speak(text: String) {
            Log.d("AIVoiceCallout", "Speaking: $text at volume=$currentVolume")
            val mappedResId = voiceResIdForText(text)
            val resId = mappedResId ?: voiceResIdOrFallback(text)
            if (mappedResId == null) {
                Log.w("AIVoiceCallout", "Unmapped cue requested, using bundled fallback: $text")
            }
            try {
                mediaPlayer?.release()
                mediaPlayer = MediaPlayer.create(context, resId)
                mediaPlayer?.apply {
                    setAudioAttributes(
                        AudioAttributes
                            .Builder()
                            .setUsage(AudioAttributes.USAGE_ASSISTANCE_SONIFICATION)
                            .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                            .build(),
                    )
                    setVolume(currentVolume, currentVolume)
                    setOnCompletionListener { 
                        it.release()
                        if (mediaPlayer == it) {
                            mediaPlayer = null
                        }
                    }
                    start()
                }
            } catch (e: Exception) {
                Log.e("AIVoice", "Audio playback failed: ${e.message}", e)
            }
        }

        fun resetSession() {
            lastElapsedMilestone = 0
        }

        fun preview() {
            previewCommandCue()
        }

        fun previewCommandCue() {
            // Cycle through available command cues to show variety
            val cue = COMMAND_VOICE_CUES[previewCycleIndex]
            speak(cue)
            previewCycleIndex = (previewCycleIndex + 1) % COMMAND_VOICE_CUES.size
        }

        fun previewCountdownCue() {
            // With elapsed model, preview an elapsed milestone announcement
            speak(PREVIEW_ELAPSED_CUE)
        }

        // Called every second with elapsed seconds since timer started.
        fun triggerCallout(elapsedSeconds: Int) {
            runtimeVoiceCueForElapsedSecond(elapsedSeconds, lastElapsedMilestone)?.let {
                speak(it)
                lastElapsedMilestone = elapsedSeconds
            }
        }

        fun shutdown() {
            mediaPlayer?.release()
            mediaPlayer = null
        }
    }
