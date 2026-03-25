import XCTest
import CryptoKit
@testable import RandomTimer

@MainActor
final class AIVoiceCalloutServiceTests: XCTestCase {
    private func makeUnusedTestAssetURL(filename: String) -> URL {
        URL(filePath: NSTemporaryDirectory()).appendingPathComponent(filename)
    }

    private func makeSut() -> AIVoiceCalloutService {
        let service = AIVoiceCalloutService(bundle: .main)
        service.resetSession()
        return service
    }

    func testTriggerCalloutElapsedMilestonesDoNotCrash() {
        let sut = makeSut()
        let catalog = loadVoiceCalloutCatalog(bundle: .main)

        catalog.elapsedCues.map(\.second).forEach { elapsed in
            sut.triggerCallout(elapsedSeconds: elapsed)
        }
    }

    func testPreviewCuesDoNotCrash() {
        let sut = makeSut()
        sut.preview()
        sut.previewCommandCue()
        sut.previewCountdownCue()
    }

    func testResetSessionAllowsElapsedMilestoneToReplay() {
        let sut = makeSut()
        sut.triggerCallout(elapsedSeconds: 30)
        sut.resetSession()
        sut.triggerCallout(elapsedSeconds: 30)
    }

    func testCommandCueScheduleDoesNotCrashAcrossLongRun() {
        let sut = makeSut()
        for elapsed in 1...180 {
            sut.triggerCallout(elapsedSeconds: elapsed)
        }
    }

    func testCatalogHasVarietyAndClearElapsedLanguage() {
        let catalog = loadVoiceCalloutCatalog(bundle: .main)

        XCTAssertGreaterThanOrEqual(catalog.elapsedCues.count, 16)
        XCTAssertGreaterThanOrEqual(catalog.commandCues.count, 20)
        XCTAssertTrue(
            catalog.elapsedCues.allSatisfy { $0.text.localizedCaseInsensitiveContains("elapsed") },
            "Elapsed cues must explicitly say elapsed so they are not mistaken for time remaining."
        )
    }

    func testEveryRuntimeCueHasBundledFilename() {
        let catalog = loadVoiceCalloutCatalog(bundle: .main)

        XCTAssertEqual(voiceFilename(for: catalog.previewElapsed.text, bundle: .main), catalog.previewElapsed.filename)
        XCTAssertTrue(catalog.elapsedCues.allSatisfy { voiceFilename(for: $0.text, bundle: .main) == $0.filename })
        XCTAssertTrue(catalog.commandCues.allSatisfy { voiceFilename(for: $0.text, bundle: .main) == $0.filename })
    }

    func testBundledVoiceAudioResolvesFromMainBundle() {
        let catalog = loadVoiceCalloutCatalog(bundle: .main)
        let missing = Set(catalog.bundledFilenames)
            .filter { bundledVoiceAudioURL(for: $0, bundle: .main) == nil }
            .sorted()

        XCTAssertTrue(missing.isEmpty, "Missing bundled voice assets: \(missing)")
    }

    func testUnknownCueFallsBackToBundledDrillInstructorClip() {
        let catalog = loadVoiceCalloutCatalog(bundle: .main)
        let fallback = voiceFilenameOrFallback(for: "Unexpected cue", bundle: .main)

        XCTAssertEqual(fallback, catalog.fallbackCommandCue.filename)
        XCTAssertNotNil(bundledVoiceAudioURL(for: fallback, bundle: .main))
    }

    func testVoiceCatalogRuntimeMapsIgnoreDuplicateKeys() {
        let catalog = VoiceCueCatalog(
            previewElapsed: .init(filename: "preview_elapsed", text: "Repeat me."),
            fallbackCommandFilename: "cmd_primary",
            elapsedCues: [
                .init(second: 30, filename: "elapsed_primary", text: "Thirty elapsed."),
                .init(second: 30, filename: "elapsed_duplicate", text: "Thirty elapsed duplicate."),
            ],
            commandCues: [
                .init(filename: "cmd_primary", text: "Repeat me."),
                .init(filename: "cmd_duplicate", text: "Repeat me."),
            ]
        )

        XCTAssertEqual(catalog.elapsedCueBySecond[30]?.filename, "elapsed_primary")
        XCTAssertEqual(catalog.filenameByText["Repeat me."], "preview_elapsed")
    }

    func testNextCommandCueAvoidsImmediateRepeatWhenPossible() {
        let cues = [
            VoiceCueCatalog.Cue(filename: "cue_a", text: "Cue A"),
            VoiceCueCatalog.Cue(filename: "cue_b", text: "Cue B"),
        ]

        let selected = nextCommandCue(from: cues, lastFilename: "cue_a") { _ in 0 }
        XCTAssertEqual(selected.filename, "cue_b")
    }

    func testShortTimersScheduleFollowupCommandCuesEarly() {
        XCTAssertEqual(initialFollowupCommandCueSecond(totalDurationSeconds: 12), .max)
        XCTAssertEqual(initialFollowupCommandCueSecond(totalDurationSeconds: 20), 10)
        XCTAssertEqual(initialFollowupCommandCueSecond(totalDurationSeconds: 40), 15)
    }

    func testRemotePackStoreInstallsAndServesRemoteVoiceAndSoundAssets() throws {
        let cacheRoot = FileManager.default.temporaryDirectory
            .appendingPathComponent("pro-audio-store-tests-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: cacheRoot) }

        let voicePayload = Data("voice-remote".utf8)
        let soundPayload = Data("sound-remote".utf8)
        let manifest = makeRemoteManifest(voicePayload: voicePayload, soundPayload: soundPayload)

        let store = ProAudioPackStore(bundle: .main, manifestURL: nil, cacheRoot: cacheRoot)
        try store.installForTesting(
            manifest: manifest,
            payloadsByKey: [
                "voice:preview_elapsed": voicePayload,
                "sound:alarm": soundPayload,
            ]
        )

        XCTAssertEqual(store.voiceCatalog().previewElapsed.text, "Fifteen seconds elapsed. Move.")
        XCTAssertEqual(store.soundCatalog().packId, "2026-04_field")
        XCTAssertEqual(
            try Data(contentsOf: XCTUnwrap(store.voiceAudioURL(for: "preview_elapsed", bundle: .main))),
            voicePayload
        )
        XCTAssertEqual(
            try Data(contentsOf: XCTUnwrap(store.soundAudioURL(for: .intense, bundle: .main))),
            soundPayload
        )
    }

    private func sha256Hex(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }

    private func makeRemoteManifest(voicePayload: Data, soundPayload: Data) -> RemoteProAudioManifest {
        RemoteProAudioManifest(
            schemaVersion: 1,
            packId: "2026-04_field",
            releaseMonth: "2026-04",
            entitlement: "pro",
            generatedAt: "2026-04-01T15:00:00Z",
            voiceCatalog: VoiceCueCatalog(
                previewElapsed: .init(filename: "preview_elapsed", text: "Fifteen seconds elapsed. Move."),
                fallbackCommandFilename: "cmd_move",
                elapsedCues: [.init(second: 15, filename: "elapsed_15s", text: "Fifteen seconds elapsed. Move.")],
                commandCues: [.init(filename: "cmd_move", text: "Move.")]
            ),
            soundCatalog: ProSoundCatalog(
                packId: "2026-04_field",
                releaseMonth: "2026-04",
                entitlement: "pro",
                sounds: [.init(soundType: "intense", filename: "alarm", durationSeconds: 4)]
            ),
            assets: [
                .init(
                    kind: .voice,
                    filename: "preview_elapsed",
                    relativePath: "packs/2026-04_field/voice/preview_elapsed.mp3",
                    url: makeUnusedTestAssetURL(filename: "preview_elapsed.mp3"),
                    sha256: sha256Hex(voicePayload),
                    bytes: voicePayload.count
                ),
                .init(
                    kind: .sound,
                    filename: "alarm",
                    relativePath: "packs/2026-04_field/sounds/alarm.mp3",
                    url: makeUnusedTestAssetURL(filename: "alarm.mp3"),
                    sha256: sha256Hex(soundPayload),
                    bytes: soundPayload.count
                ),
            ]
        )
    }
}
