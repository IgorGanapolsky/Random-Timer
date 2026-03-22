package com.iganapolsky.randomtimer.service
import kotlin.random.Random

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.util.Log
import com.iganapolsky.randomtimer.R
import dagger.hilt.android.qualifiers.ApplicationContext
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

internal data class VoiceCandidate(
    val name: String,
    val locale: Locale,
)

internal data class VoiceCue(
    val filename: String,
    val text: String,
)

internal data class ElapsedVoiceCue(
    val second: Int,
    val filename: String,
    val text: String,
)

internal data class VoiceCueCatalog(
    val previewElapsed: VoiceCue,
    val fallbackCommandFilename: String,
    val elapsedCues: List<ElapsedVoiceCue>,
    val commandCues: List<VoiceCue>,
) {
    val elapsedCueBySecond: Map<Int, ElapsedVoiceCue>
        get() = elapsedCues.associateBy { it.second }

    val fallbackCommandCue: VoiceCue
        get() = commandCues.firstOrNull { it.filename == fallbackCommandFilename } ?: commandCues.firstOrNull() ?: previewElapsed

    val filenameByText: Map<String, String>
        get() =
            buildMap {
                put(previewElapsed.text, previewElapsed.filename)
                elapsedCues.forEach { put(it.text, it.filename) }
                commandCues.forEach { put(it.text, it.filename) }
            }
}

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

        companion object {
            val preferredVoiceNames = listOf("en-us-x-tpf", "en-us-x-sfg", "en-US-language")
        }

        fun speak(text: String) {
            Log.d("AIVoiceCallout", "Speaking: $text")
            val mappedResId = voiceResIdForText(text)
            val resId = mappedResId ?: voiceResIdOrFallback(text)
            if (mappedResId == null) {
                Log.w("AIVoiceCallout", "Unmapped cue requested, using bundled fallback: $text")
            }
            try {
                val attrs =
                    AudioAttributes
                        .Builder()
                        .setUsage(AudioAttributes.USAGE_ALARM)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build()
                val mp =
                    MediaPlayer().apply {
                        setAudioAttributes(attrs)
                        val afd = context.resources.openRawResourceFd(resId)
                        setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
                        afd.close()
                        prepare()
                    }
                mp.setOnCompletionListener { it.release() }
                mp.start()
            } catch (e: Exception) {
                android.util.Log.e("AIVoice", "Audio playback failed: ${e.message}")
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

        fun previewCountdownCue() {
            // With elapsed model, preview an elapsed milestone announcement
            speak(PREVIEW_ELAPSED_CUE)
        }

        fun triggerCallout(elapsedSeconds: Int) {
            runtimeVoiceCueForElapsedSecond(elapsedSeconds, lastElapsedMilestone)?.let {
                speak(it)
                lastElapsedMilestone = elapsedSeconds
            }
        }

        fun shutdown() {
            // No-op: drill sergeant callouts use bundled audio clips instead of system TTS.
        }
    }
