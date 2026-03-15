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

internal val RUNTIME_COMMAND_CUES_BY_ELAPSED_SECOND =
    mapOf(
        30 to PREVIEW_COMMAND_CUE,
        60 to "Move now.",
        90 to "Keep pressure.",
        120 to "Drive forward.",
        180 to "Push the pace.",
        300 to "Push through.",
        600 to "Reset and breathe.",
    )

internal const val DEFAULT_VOICE_FALLBACK_CUE = PREVIEW_COMMAND_CUE

internal fun runtimeVoiceCueForElapsedSecond(
    elapsedSeconds: Int,
    lastElapsedMilestone: Int,
): String? {
    if (elapsedSeconds == lastElapsedMilestone) return null
    return RUNTIME_COMMAND_CUES_BY_ELAPSED_SECOND[elapsedSeconds]
}

internal fun voiceResIdForText(text: String): Int? =
    when (text) {
        PREVIEW_COMMAND_CUE -> R.raw.cmd_stay_sharp
        "Move now." -> R.raw.cmd_move_now
        "Keep pressure." -> R.raw.cmd_keep_pressure
        "Drive forward." -> R.raw.cmd_drive_forward
        "Push the pace." -> R.raw.cmd_push_pace
        "Push through." -> R.raw.cmd_push_through
        "Reset and breathe." -> R.raw.cmd_reset_breathe
        PREVIEW_ELAPSED_CUE -> R.raw.preview_elapsed
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
                mediaPlayer =
                    MediaPlayer().apply {
                        val afd =
                            context.resources.openRawResourceFd(resId)
                                ?: throw IllegalStateException("Could not open voice resource")
                        setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
                        afd.close()
                        setAudioAttributes(
                            AudioAttributes
                                .Builder()
                                .setUsage(AudioAttributes.USAGE_ALARM)
                                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                                .build(),
                        )
                        prepare()
                    }
                mediaPlayer?.apply {
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
            speak(PREVIEW_COMMAND_CUE)
        }

        fun previewElapsedMilestoneCue() {
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
