package com.iganapolsky.randomtimer.service

import com.google.common.truth.Truth.assertThat
import org.junit.Test
import java.nio.file.Paths
import java.util.Locale

class AIVoiceCalloutManagerSelectionTest {
    @Test
    fun `selectPreferredVoice ignores non english male voices`() {
        val selected =
            selectPreferredVoice(
                listOf(
                    VoiceCandidate("hi-IN-x-cfn#male_3-local", Locale("hi", "IN")),
                    VoiceCandidate("en-us-x-sfg#male_1-local", Locale.US),
                ),
            )

        assertThat(selected?.name).isEqualTo("en-us-x-sfg#male_1-local")
    }

    @Test
    fun `selectPreferredVoice returns null when only non english voices are available`() {
        val selected =
            selectPreferredVoice(
                listOf(
                    VoiceCandidate("hi-IN-x-cfn#male_3-local", Locale("hi", "IN")),
                    VoiceCandidate("es-es-x-eef-local", Locale("es", "ES")),
                ),
            )

        assertThat(selected).isNull()
    }

    @Test
    fun parseVoiceCalloutCatalogReadsSharedGeneratedAsset() {
        val path = Paths.get("src/main/assets/voice_callouts.json")
        val catalog = parseVoiceCalloutCatalog(path.toFile().readText())

        assertThat(catalog.elapsedCues.size).isAtLeast(12)
        assertThat(catalog.commandCues.size).isAtLeast(20)
        assertThat(catalog.elapsedCues.all { it.text.contains("elapsed", ignoreCase = true) }).isTrue()
    }

    @Test
    fun femalePreviewSamplesExistOnDisk() {
        val required =
            listOf(
                "female_preview_move_with_a_purpose.mp3",
                "female_preview_no_hesitation_move.mp3",
                "female_preview_stay_in_the_fight.mp3",
                "female_preview_push_through_dont_you_dare_coast.mp3",
                "female_preview_thirty_seconds_elapsed_stay_locked_in.mp3",
            )

        val rawDir = Paths.get("src/main/res/raw")
        val missing = required.filterNot { rawDir.resolve(it).toFile().exists() }

        assertThat(missing).isEmpty()
    }

    @Test
    fun nextCommandCueAvoidsImmediateRepeatsWhenMultipleCuesExist() {
        val cues =
            listOf(
                VoiceCue(filename = "cue_a", text = "Cue A"),
                VoiceCue(filename = "cue_b", text = "Cue B"),
            )

        val selected = nextCommandCue(cues, lastFilename = "cue_a") { 0 }

        assertThat(selected.filename).isEqualTo("cue_b")
    }

    @Test
    fun runtimeVoiceCueForElapsedMarkReturnsConfiguredElapsedAnnouncements() {
        val catalog =
            VoiceCueCatalog(
                previewElapsed = VoiceCue(filename = "preview_elapsed", text = "Preview"),
                fallbackCommandFilename = "cmd_a",
                elapsedCues =
                    listOf(
                        ElapsedVoiceCue(second = 15, filename = "elapsed_15s", text = "Fifteen seconds elapsed."),
                        ElapsedVoiceCue(second = 30, filename = "elapsed_30s", text = "Thirty seconds elapsed."),
                        ElapsedVoiceCue(second = 60, filename = "elapsed_60s", text = "One minute elapsed."),
                    ),
                commandCues = listOf(VoiceCue(filename = "cmd_a", text = "Move.")),
            )

        assertThat(runtimeVoiceCueForElapsedMark(14, lastElapsedMilestone = 0, catalog = catalog)).isNull()
        assertThat(runtimeVoiceCueForElapsedMark(15, lastElapsedMilestone = 0, catalog = catalog)?.filename).isEqualTo("elapsed_15s")
        assertThat(runtimeVoiceCueForElapsedMark(30, lastElapsedMilestone = 0, catalog = catalog)?.filename).isEqualTo("elapsed_30s")
        assertThat(runtimeVoiceCueForElapsedMark(60, lastElapsedMilestone = 0, catalog = catalog)?.filename).isEqualTo("elapsed_60s")
    }

    @Test
    fun shortTimersScheduleFollowupCommandCuesEarly() {
        assertThat(initialFollowupCommandCueSecond(12)).isEqualTo(Int.MAX_VALUE)
        assertThat(initialFollowupCommandCueSecond(20)).isEqualTo(Int.MAX_VALUE)
        assertThat(initialFollowupCommandCueSecond(40)).isEqualTo(15)
    }

    @Test
    fun parseRemoteProAudioManifestKeepsHostedCatalogsAndAssetIntegrityMetadata() {
        val manifest =
            parseRemoteProAudioManifest(
                """
                {
                  "schemaVersion": 1,
                  "packId": "2026-04_field",
                  "releaseMonth": "2026-04",
                  "entitlement": "pro",
                  "generatedAt": "2026-04-01T15:00:00Z",
                  "voiceCatalog": {
                    "previewElapsed": {"filename": "preview_elapsed", "text": "Fifteen seconds elapsed. Move."},
                    "fallbackCommandFilename": "cmd_move",
                    "elapsedCues": [{"second": 15, "filename": "elapsed_15s", "text": "Fifteen seconds elapsed. Move."}],
                    "commandCues": [{"filename": "cmd_move", "text": "Move."}]
                  },
                  "soundCatalog": {
                    "packId": "2026-04_field",
                    "releaseMonth": "2026-04",
                    "entitlement": "pro",
                    "sounds": [{"soundType": "intense", "filename": "alarm"}]
                  },
                  "assets": [
                    {
                      "kind": "voice",
                      "filename": "preview_elapsed",
                      "relativePath": "packs/2026-04_field/voice/preview_elapsed.mp3",
                      "url": "https://example.com/preview_elapsed.mp3",
                      "sha256": "abcd",
                      "bytes": 12
                    }
                  ]
                }
                """.trimIndent(),
            )

        assertThat(manifest.packId).isEqualTo("2026-04_field")
        assertThat(manifest.voiceCatalog.previewElapsed.text).contains("elapsed")
        assertThat(manifest.soundCatalog.filenameByType[com.iganapolsky.randomtimer.domain.model.SoundType.INTENSE]).isEqualTo("alarm")
        assertThat(manifest.assets.single().relativePath).isEqualTo("packs/2026-04_field/voice/preview_elapsed.mp3")
    }
}
