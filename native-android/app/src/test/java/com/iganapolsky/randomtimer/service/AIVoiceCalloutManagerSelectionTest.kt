package com.iganapolsky.randomtimer.service

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.VoiceGender
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
                gender = VoiceGender.MALE,
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
                gender = VoiceGender.MALE,
            )

        assertThat(selected).isNull()
    }

    @Test
    fun `selectPreferredVoice prefers english female voices when requested`() {
        val selected =
            selectPreferredVoice(
                listOf(
                    VoiceCandidate("en-us-x-sfg#male_1-local", Locale.US),
                    VoiceCandidate("en-us-x-tpc#female_1-local", Locale.US),
                ),
                gender = VoiceGender.FEMALE,
            )

        assertThat(selected?.name).isEqualTo("en-us-x-tpc#female_1-local")
    }

    @Test
    fun `voicePlaybackMode uses system synthesis for female voices`() {
        assertThat(voicePlaybackMode(VoiceGender.MALE)).isEqualTo(VoicePlaybackMode.BUNDLED_ASSET)
        assertThat(voicePlaybackMode(VoiceGender.FEMALE)).isEqualTo(VoicePlaybackMode.SYSTEM_SYNTHESIZED)
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
    fun runtimeVoiceCueForMinuteMarkOnlyReturnsMinuteElapsedAnnouncements() {
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

        assertThat(runtimeVoiceCueForMinuteMark(15, lastElapsedMilestone = 0, catalog = catalog)).isNull()
        assertThat(runtimeVoiceCueForMinuteMark(30, lastElapsedMilestone = 0, catalog = catalog)).isNull()
        assertThat(runtimeVoiceCueForMinuteMark(60, lastElapsedMilestone = 0, catalog = catalog)?.filename).isEqualTo("elapsed_60s")
    }

    @Test
    fun shortTimersScheduleFollowupCommandCuesEarly() {
        assertThat(initialFollowupCommandCueSecond(12)).isEqualTo(Int.MAX_VALUE)
        assertThat(initialFollowupCommandCueSecond(20)).isEqualTo(Int.MAX_VALUE)
        assertThat(initialFollowupCommandCueSecond(40)).isEqualTo(30)
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
