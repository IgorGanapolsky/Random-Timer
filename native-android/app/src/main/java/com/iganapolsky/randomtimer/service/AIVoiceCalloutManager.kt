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

internal const val PREVIEW_ELAPSED_CUE = "Thirty seconds. Stay locked in."

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

internal val COMMAND_VOICE_CUES =
    listOf(
        "Stay sharp.",
        "Reset. Breathe.",
    )

internal const val DEFAULT_VOICE_FALLBACK_CUE = "Stay sharp."

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
        "Move now." -> R.raw.cmd_move_now
        "Stay sharp." -> R.raw.cmd_stay_sharp
        "Reset. Breathe." -> R.raw.cmd_reset_breathe
        "Push the pace." -> R.raw.cmd_push_pace
        "Drive forward." -> R.raw.cmd_drive_forward
        "Keep pressure." -> R.raw.cmd_keep_pressure
        "Push through it." -> R.raw.cmd_push_through
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
        private var nextCommandCueAt = 0
        private var lastCommandCueAt = 0

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
            speak(PREVIEW_ELAPSED_CUE)
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
            return ELAPSED_VOICE_CUES_BY_SECOND[elapsed]
        }

        private fun shouldFireCommandCue(elapsedSeconds: Int): Boolean {
            if (nextCommandCueAt == 0) {
                nextCommandCueAt = Random.nextInt(8, 21)
            }
            return elapsedSeconds >= nextCommandCueAt
        }

        private fun randomCommandCue(): String = COMMAND_VOICE_CUES[Random.nextInt(COMMAND_VOICE_CUES.size)]

        fun shutdown() {
            // No-op: drill sergeant callouts use bundled audio clips instead of system TTS.
        }
    }
