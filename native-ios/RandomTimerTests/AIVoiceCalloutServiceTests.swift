import XCTest
import CryptoKit
@testable import RandomTimer

@MainActor
final class AIVoiceCalloutServiceTests: XCTestCase {
    private final class CounterBox {
        var value = 0
    }

    private func makeUnusedTestAssetURL(filename: String) -> URL {
        URL(filePath: NSTemporaryDirectory()).appendingPathComponent(filename)
    }

    private func makeSut() -> AIVoiceCalloutService {
        let service = AIVoiceCalloutService(bundle: .main)
        service.resetSession()
        return service
    }

    private func makeSut(counter: CounterBox) -> AIVoiceCalloutService {
        let service = AIVoiceCalloutService(
            bundle: .main,
            activateAudioSession: { counter.value += 1 }
        )
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
        sut.previewCommandCue(gender: .female)
        sut.previewCountdownCue(gender: .female)
    }

    func testVoicePlaybackModeUsesSystemSynthesisForFemaleVoice() {
        XCTAssertEqual(voicePlaybackMode(for: .male), .bundledAsset)
        XCTAssertEqual(voicePlaybackMode(for: .female), .systemSynthesized)
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

        XCTAssertGreaterThanOrEqual(catalog.elapsedCues.count, 12)
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
        XCTAssertEqual(initialFollowupCommandCueSecond(totalDurationSeconds: 20), .max)
        XCTAssertEqual(initialFollowupCommandCueSecond(totalDurationSeconds: 40), 30)
    }

    func testPlaybackReactivatesAudioSessionAfterSessionBegin() {
        let counter = CounterBox()
        let sut = makeSut(counter: counter)

        sut.beginSession(totalDurationSeconds: 60)
        sut.previewCountdownCue()

        XCTAssertGreaterThanOrEqual(
            counter.value,
            2,
            "Voice playback must reactivate AVAudioSession before cue playback."
        )
    }

    func testPreviewCommandCueUpdatesCurrentGender() {
        let sut = makeSut()

        sut.previewCommandCue(gender: .female)

        XCTAssertEqual(sut.currentGender, .female)
    }

    func testBeginSessionUsesConfiguredGender() {
        let sut = makeSut()

        sut.beginSession(totalDurationSeconds: 60, gender: .female)

        XCTAssertEqual(sut.currentGender, .female)
    }

    func testTimerCalloutsUseCommandsAtThirtySecondsAndElapsedOnlyOnMinuteMarks() {
        let sut = makeSut()

        sut.beginSession(totalDurationSeconds: 120)
        sut.triggerCallout(elapsedSeconds: 15)
        let beforeThirty = sut._stateSnapshotForTesting()
        XCTAssertEqual(beforeThirty.lastElapsedMilestone, 0)
        XCTAssertEqual(beforeThirty.nextCommandCueAt, 30)
        XCTAssertNil(beforeThirty.lastCommandCueFilename)

        sut.triggerCallout(elapsedSeconds: 30)
        let atThirty = sut._stateSnapshotForTesting()
        XCTAssertEqual(atThirty.lastElapsedMilestone, 0)
        XCTAssertEqual(atThirty.nextCommandCueAt, 60)
        XCTAssertNotNil(atThirty.lastCommandCueFilename)

        sut.triggerCallout(elapsedSeconds: 60)
        let atSixty = sut._stateSnapshotForTesting()
        XCTAssertEqual(atSixty.lastElapsedMilestone, 60)
        XCTAssertEqual(atSixty.nextCommandCueAt, 90)
    }

    func testFirstTimedCalloutReactivatesAudioSessionBeforePlayback() {
        let counter = CounterBox()
        let sut = makeSut(counter: counter)

        sut.beginSession(totalDurationSeconds: 60)
        sut.triggerCallout(elapsedSeconds: 30)

        XCTAssertGreaterThanOrEqual(
            counter.value,
            1,
            "Timed voice playback must reactivate AVAudioSession before speaking."
        )
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
