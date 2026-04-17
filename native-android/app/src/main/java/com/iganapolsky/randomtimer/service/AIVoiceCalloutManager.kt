package com.iganapolsky.randomtimer.service
import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.util.Log
import com.iganapolsky.randomtimer.domain.model.VoiceGender
import dagger.hilt.android.qualifiers.ApplicationContext
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.random.Random

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

private data class VoicePlaybackSource(
    val remotePath: String? = null,
    val resourceId: Int = 0,
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

private const val VOICE_CATALOG_ASSET = "voice_callouts.json"

private object VoicePreviewSampleCatalog {
    val maleCommandFilenames =
        listOf(
            "cmd_move_with_a_purpose",
            "cmd_stay_locked_in",
            "cmd_no_hesitation_move",
            "cmd_sound_off_and_drive",
            "cmd_snap_back_and_drive",
            "cmd_stay_disciplined",
            "cmd_keep_your_bearing",
            "cmd_reset_and_attack",
            "cmd_sharp_movement_sharp_focus",
            "cmd_stay_in_the_fight",
        )

    const val maleElapsedFilename = "preview_elapsed"

    val femaleCommandFilenames =
        listOf(
            "female_cmd_move_with_a_purpose",
            "female_cmd_no_hesitation_move",
            "female_cmd_stay_in_the_fight",
            "female_cmd_push_pace",
            "female_cmd_keep_tempo_high",
            "female_cmd_finish_rep_keep_pushing",
            "female_cmd_drive_forward",
            "female_cmd_own_this_rep",
            "female_cmd_pick_it_up",
            "female_cmd_strong_feet_strong_pace",
        )

    const val femaleElapsedFilename = "female_preview_elapsed"
}

private val fallbackVoiceCueCatalog =
    VoiceCueCatalog(
        previewElapsed = VoiceCue(filename = "preview_elapsed", text = "Thirty seconds elapsed. Move with a purpose."),
        fallbackCommandFilename = "cmd_move_with_a_purpose",
        elapsedCues =
            listOf(
                ElapsedVoiceCue(second = 60, filename = "elapsed_60s", text = "One minute elapsed. Keep pressure on."),
            ),
        commandCues =
            listOf(
                VoiceCue(filename = "cmd_move_with_a_purpose", text = "Move with a purpose."),
                VoiceCue(filename = "cmd_stay_locked_in", text = "Stay locked in."),
            ),
    )

internal fun parseVoiceCalloutCatalog(json: String): VoiceCueCatalog {
    val root = JSONObject(json)
    return VoiceCueCatalog(
        previewElapsed = root.getJSONObject("previewElapsed").toVoiceCue(),
        fallbackCommandFilename = root.getString("fallbackCommandFilename"),
        elapsedCues = root.getJSONArray("elapsedCues").toElapsedVoiceCues(),
        commandCues = root.getJSONArray("commandCues").toVoiceCues(),
    )
}

private fun JSONObject.toVoiceCue(): VoiceCue =
    VoiceCue(
        filename = getString("filename"),
        text = getString("text"),
    )

private fun JSONObject.toElapsedVoiceCue(): ElapsedVoiceCue =
    ElapsedVoiceCue(
        second = getInt("second"),
        filename = getString("filename"),
        text = getString("text"),
    )

private fun JSONArray.toVoiceCues(): List<VoiceCue> =
    buildList {
        for (index in 0 until length()) {
            add(getJSONObject(index).toVoiceCue())
        }
    }

private fun JSONArray.toElapsedVoiceCues(): List<ElapsedVoiceCue> =
    buildList {
        for (index in 0 until length()) {
            add(getJSONObject(index).toElapsedVoiceCue())
        }
    }

internal fun loadVoiceCalloutCatalog(context: Context): VoiceCueCatalog =
    runCatching {
        context.assets
            .open(VOICE_CATALOG_ASSET)
            .bufferedReader()
            .use { parseVoiceCalloutCatalog(it.readText()) }
    }.getOrElse { fallbackVoiceCueCatalog }

internal fun voiceResIdForText(
    context: Context,
    text: String,
    catalog: VoiceCueCatalog,
): Int? = catalog.filenameByText[text]?.let { context.resources.getIdentifier(it, "raw", context.packageName) }.takeIf { it != 0 }

internal fun voiceResIdOrFallback(
    context: Context,
    text: String,
    catalog: VoiceCueCatalog,
): Int {
    val fallback = catalog.filenameByText[text] ?: catalog.fallbackCommandCue.filename
    return context.resources.getIdentifier(fallback, "raw", context.packageName)
}

internal fun genderedVoiceFilename(
    filename: String,
    gender: VoiceGender,
): String =
    when (gender) {
        VoiceGender.MALE -> filename
        VoiceGender.FEMALE -> if (filename.startsWith("female_")) filename else "female_$filename"
    }

internal fun runtimeVoiceCueForElapsedSecond(
    elapsedSeconds: Int,
    lastElapsedMilestone: Int,
    catalog: VoiceCueCatalog,
): VoiceCue? {
    if (elapsedSeconds == lastElapsedMilestone) return null
    return catalog.elapsedCueBySecond[elapsedSeconds]?.let { VoiceCue(filename = it.filename, text = it.text) }
}

/**
 * Returns a bundled "time elapsed" announcement only on full-minute marks (60, 120, …).
 * Sub-minute rows in JSON are ignored here so command coaching stays on its own cadence.
 */
internal fun runtimeVoiceCueForElapsedMark(
    elapsedSeconds: Int,
    lastElapsedMilestone: Int,
    catalog: VoiceCueCatalog,
): VoiceCue? {
    if (elapsedSeconds <= 0) {
        return null
    }
    if (elapsedSeconds % 60 != 0) {
        return null
    }
    return runtimeVoiceCueForElapsedSecond(
        elapsedSeconds = elapsedSeconds,
        lastElapsedMilestone = lastElapsedMilestone,
        catalog = catalog,
    )
}

internal fun nextCommandCue(
    cues: List<VoiceCue>,
    lastFilename: String?,
    pickIndex: (Int) -> Int,
): VoiceCue {
    if (cues.isEmpty()) {
        return fallbackVoiceCueCatalog.fallbackCommandCue
    }
    if (cues.size == 1) {
        return cues[0]
    }

    val boundedIndex = pickIndex(cues.size).coerceIn(0, cues.size - 1)
    val candidate = cues[boundedIndex]
    if (candidate.filename != lastFilename) {
        return candidate
    }
    return cues[(boundedIndex + 1) % cues.size]
}

internal fun nextPreviewCueFilename(
    filenames: List<String>,
    lastFilename: String?,
    usedFilenames: MutableSet<String>,
    pickIndex: (Int) -> Int,
): String {
    if (filenames.isEmpty()) {
        return fallbackVoiceCueCatalog.fallbackCommandFilename
    }
    if (filenames.size == 1) {
        val only = filenames[0]
        usedFilenames.clear()
        usedFilenames.add(only)
        return only
    }

    var pool = filenames.filter { it !in usedFilenames }
    if (pool.isEmpty()) {
        usedFilenames.clear()
        pool = filenames.filter { it != lastFilename }.ifEmpty { filenames }
    }

    val boundedIndex = pickIndex(pool.size).coerceIn(0, pool.size - 1)
    val candidate = pool[boundedIndex]
    val selected =
        if (candidate == lastFilename && pool.size > 1) {
            pool[(boundedIndex + 1) % pool.size]
        } else {
            candidate
        }
    usedFilenames.add(selected)
    return selected
}

internal fun initialFollowupCommandCueSecond(totalDurationSeconds: Int): Int =
    when {
        totalDurationSeconds <= 30 -> Int.MAX_VALUE
        else -> 30
    }

@Singleton
class AIVoiceCalloutManager
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
        private val packStore: ProAudioPackStore,
    ) {
        private var lastElapsedMilestone = 0
        private var mediaPlayer: MediaPlayer? = null
        private var currentVolume: Float = 1.0f
        private var lastCommandCueFilename: String? = null
        private val usedCommandCueFilenames = mutableSetOf<String>()
        private val lastPreviewCommandFilenameByGender = mutableMapOf<VoiceGender, String?>()
        private val usedPreviewCommandFilenamesByGender =
            mutableMapOf(
                VoiceGender.MALE to mutableSetOf<String>(),
                VoiceGender.FEMALE to mutableSetOf<String>(),
            )
        private var nextCommandCueAt = 0

        /** Current voice gender for the active session. */
        var currentGender: VoiceGender = VoiceGender.MALE
            private set

        companion object {
            val preferredVoiceNames = listOf("en-us-x-tpf", "en-us-x-sfg", "en-US-language")
        }

        fun setVolume(volume: Float) {
            currentVolume = volume.coerceIn(0f, 1f)
            mediaPlayer?.setVolume(currentVolume, currentVolume)
        }

        private fun stopPlayback() {
            val player = mediaPlayer ?: return
            runCatching {
                if (player.isPlaying) {
                    player.stop()
                }
            }
            player.release()
            if (mediaPlayer == player) {
                mediaPlayer = null
            }
        }

        fun speak(text: String) {
            val catalog = packStore.voiceCatalog()
            val mappedFilename = catalog.filenameByText[text]
            val baseFilename = mappedFilename ?: catalog.fallbackCommandCue.filename
            val filename = genderedVoiceFilename(baseFilename, currentGender)
            val directResId = context.resources.getIdentifier(filename, "raw", context.packageName)
            val fallbackFilename = genderedVoiceFilename(catalog.fallbackCommandCue.filename, currentGender)
            val fallbackResId = context.resources.getIdentifier(fallbackFilename, "raw", context.packageName)
            val resId = directResId.takeIf { it != 0 } ?: fallbackResId.takeIf { it != 0 } ?: voiceResIdOrFallback(context, text, catalog)
            if (mappedFilename == null) {
                Log.w("AIVoiceCallout", "Unmapped cue requested, using bundled fallback: $text")
            }

            playVoiceFile(filename = filename, fallbackResId = resId, cueText = text)
        }

        fun resetSession() {
            stopPlayback()
            lastElapsedMilestone = 0
            lastCommandCueFilename = null
            usedCommandCueFilenames.clear()
            lastPreviewCommandFilenameByGender.clear()
            usedPreviewCommandFilenamesByGender.values.forEach { it.clear() }
            nextCommandCueAt = 0
            currentGender = VoiceGender.MALE
        }

        fun preview() {
            previewCommandCue(currentGender)
        }

        fun previewCommandCue(gender: VoiceGender = currentGender) {
            currentGender = gender

            val previewPool =
                if (gender == VoiceGender.FEMALE) {
                    VoicePreviewSampleCatalog.femaleCommandFilenames
                } else {
                    VoicePreviewSampleCatalog.maleCommandFilenames
                }
            val usedFilenames =
                usedPreviewCommandFilenamesByGender.getOrPut(gender) {
                    mutableSetOf()
                }
            val previewFilename =
                nextPreviewCueFilename(
                    filenames = previewPool,
                    lastFilename = lastPreviewCommandFilenameByGender[gender] ?: null,
                    usedFilenames = usedFilenames,
                ) { upperBound ->
                    Random.nextInt(upperBound)
                }
            lastPreviewCommandFilenameByGender[gender] = previewFilename
            playVoiceFile(
                filename = previewFilename,
                fallbackResId = 0,
                cueText =
                    if (gender == VoiceGender.FEMALE) {
                        "Female preview command sample"
                    } else {
                        "Male preview command sample"
                    },
            )
        }

        fun previewCountdownCue(gender: VoiceGender = currentGender) {
            currentGender = gender

            playVoiceFile(
                filename =
                    if (gender == VoiceGender.FEMALE) {
                        VoicePreviewSampleCatalog.femaleElapsedFilename
                    } else {
                        VoicePreviewSampleCatalog.maleElapsedFilename
                    },
                fallbackResId = 0,
                cueText =
                    if (gender == VoiceGender.FEMALE) {
                        "Female preview elapsed sample"
                    } else {
                        "Male preview elapsed sample"
                    },
            )
        }

        fun beginSession(
            totalDurationSeconds: Int,
            gender: VoiceGender = VoiceGender.MALE,
        ) {
            currentGender = gender
            nextCommandCueAt = initialFollowupCommandCueSecond(totalDurationSeconds)
        }

        private fun playVoiceFile(
            filename: String,
            fallbackResId: Int,
            cueText: String,
        ) {
            val source = resolvePlaybackSource(filename, fallbackResId)
            if (source == null) {
                Log.e("AIVoiceCallout", "Missing bundled voice asset for cue: $cueText")
                return
            }

            try {
                stopPlayback()
                val preparedPlayer = buildVoicePlayer(source, cueText) ?: return
                mediaPlayer = preparedPlayer
                startVoicePlayback(preparedPlayer)
            } catch (e: Exception) {
                Log.e("AIVoiceCallout", "Audio playback failed: ${e.message}", e)
            }
        }

        private fun buildVoicePlayer(
            source: VoicePlaybackSource,
            cueText: String,
        ): MediaPlayer? =
            MediaPlayer().apply {
                setAudioAttributes(
                    AudioAttributes
                        .Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build(),
                )
                if (!setVoiceDataSource(source, cueText)) {
                    release()
                    return null
                }
                prepare()
            }

        private fun startVoicePlayback(player: MediaPlayer) {
            player.setVolume(currentVolume, currentVolume)
            player.setOnCompletionListener {
                it.release()
                if (mediaPlayer == it) {
                    mediaPlayer = null
                }
            }
            player.start()
        }

        private fun resolvePlaybackSource(
            filename: String,
            fallbackResId: Int,
        ): VoicePlaybackSource? {
            val remoteFile = packStore.voiceFile(filename)
            if (remoteFile != null) {
                return VoicePlaybackSource(remotePath = remoteFile.absolutePath)
            }

            val bundledResId = context.resources.getIdentifier(filename, "raw", context.packageName)
            val resolvedResId = bundledResId.takeIf { it != 0 } ?: fallbackResId
            return resolvedResId.takeIf { it != 0 }?.let { VoicePlaybackSource(resourceId = it) }
        }

        private fun MediaPlayer.setVoiceDataSource(
            source: VoicePlaybackSource,
            cueText: String,
        ): Boolean {
            source.remotePath?.let {
                setDataSource(it)
                return true
            }

            val afd = context.resources.openRawResourceFd(source.resourceId)
            if (afd == null) {
                Log.e("AIVoiceCallout", "Missing raw voice asset for cue: $cueText")
                return false
            }

            afd.use {
                setDataSource(it.fileDescriptor, it.startOffset, it.length)
            }
            return true
        }

        fun triggerCallout(elapsedSeconds: Int) {
            val catalog = packStore.voiceCatalog()
            runtimeVoiceCueForElapsedMark(elapsedSeconds, lastElapsedMilestone, catalog)?.let {
                speak(it.text)
                lastElapsedMilestone = elapsedSeconds
                if (nextCommandCueAt <= elapsedSeconds) {
                    nextCommandCueAt = elapsedSeconds + 30
                }
                return
            }
            if (shouldFireCommandCue(elapsedSeconds)) {
                val cue = randomCommandCue()
                speak(cue.text)
                lastCommandCueFilename = cue.filename
                nextCommandCueAt = elapsedSeconds + 30
            }
        }

        private fun shouldFireCommandCue(elapsedSeconds: Int): Boolean {
            if (nextCommandCueAt == 0) {
                nextCommandCueAt = 30
            }
            if (nextCommandCueAt == Int.MAX_VALUE) {
                return false
            }
            return elapsedSeconds >= nextCommandCueAt
        }

        private fun randomCommandCue(): VoiceCue {
            val catalog = packStore.voiceCatalog()
            val available = catalog.commandCues.filter { it.filename !in usedCommandCueFilenames }
            val pool =
                available.ifEmpty {
                    // All cues used — reset and exclude only the last one
                    usedCommandCueFilenames.clear()
                    catalog.commandCues
                        .filter { it.filename != lastCommandCueFilename }
                        .ifEmpty { catalog.commandCues }
                }
            val cue =
                nextCommandCue(pool, lastCommandCueFilename) { upperBound ->
                    Random.nextInt(upperBound)
                }
            lastCommandCueFilename = cue.filename
            usedCommandCueFilenames.add(cue.filename)
            return cue
        }

        fun shutdown() {
            stopPlayback()
        }
    }
