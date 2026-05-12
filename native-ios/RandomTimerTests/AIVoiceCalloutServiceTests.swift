import XCTest
import CryptoKit
import AVFoundation
@testable import RandomTimer

private final class CounterBox {
    var value = 0
}

private final class FakeBackgroundVoiceKeepAliveEngine: BackgroundVoiceKeepAliveEngine {
    let mainMixerNode = AVAudioMixerNode()
    private(set) var isRunning = false
    private(set) var attachedNodes = 0
    private(set) var connectedNodes = 0
    private(set) var prepareCalls = 0
    private(set) var startCalls = 0
    private(set) var stopCalls = 0
    private(set) var resetCalls = 0
    var startError: Error?

    func attach(_ node: AVAudioNode) {
        attachedNodes += 1
    }

    func connect(_ node1: AVAudioNode, to node2: AVAudioNode, format: AVAudioFormat?) {
        connectedNodes += 1
    }

    func prepare() {
        prepareCalls += 1
    }

    func start() throws {
        startCalls += 1
        if let startError {
            throw startError
        }
        isRunning = true
    }

    func stop() {
        stopCalls += 1
        isRunning = false
    }

    func reset() {
        resetCalls += 1
    }
}

private func makeUnusedTestAssetURL(filename: String) -> URL {
    URL(filePath: NSTemporaryDirectory()).appendingPathComponent(filename)
}

@MainActor
private func makeVoiceCalloutService() -> AIVoiceCalloutService {
    let service = AIVoiceCalloutService(bundle: .main)
    service.resetSession()
    return service
}

@MainActor
private func makeVoiceCalloutService(counter: CounterBox) -> AIVoiceCalloutService {
    let service = AIVoiceCalloutService(
        bundle: .main,
        activateAudioSession: { counter.value += 1 }
    )
    service.resetSession()
    return service
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

@MainActor
final class AIVoiceCalloutServiceTests: XCTestCase {
    func testTriggerCalloutElapsedMilestonesDoNotCrash() {
        let sut = makeVoiceCalloutService()
        let catalog = loadVoiceCalloutCatalog(bundle: .main)

        catalog.elapsedCues.map(\.second).forEach { elapsed in
            sut.triggerCallout(elapsedSeconds: elapsed)
        }
    }

    func testPreviewCuesDoNotCrash() {
        let sut = makeVoiceCalloutService()
        sut.preview()
        sut.previewCommandCue()
        sut.previewCountdownCue()
    }

    func testFemalePreviewSamplesResolveFromMainBundle() {
        let filenames = [
            "female/cmd_move_with_a_purpose",
            "female/cmd_stay_locked_in",
            "female/cmd_no_hesitation_move",
            "female/cmd_sound_off_and_drive",
            "female/cmd_snap_back_and_drive",
            "female/cmd_stay_disciplined",
            "female/cmd_keep_your_bearing",
            "female/cmd_reset_and_attack",
            "female/cmd_sharp_movement_sharp_focus",
            "female/cmd_stay_in_the_fight",
            "female/cmd_push_pace",
            "female/cmd_keep_tempo_high",
            "female/cmd_finish_rep_keep_pushing",
            "female/cmd_drive_forward",
            "female/cmd_own_this_rep",
            "female/cmd_pick_it_up",
            "female/cmd_strong_feet_strong_pace",
            "female/preview_elapsed",
        ]

        let missing = filenames.filter { bundledVoiceAudioURL(for: $0, bundle: .main) == nil }
        XCTAssertTrue(missing.isEmpty, "Missing female preview samples: \(missing)")
    }

    func testMalePreviewSamplesResolveFromMainBundle() {
        let filenames = [
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
            "cmd_push_pace",
            "cmd_keep_tempo_high",
            "cmd_finish_rep_keep_pushing",
            "cmd_drive_forward",
            "cmd_own_this_rep",
            "cmd_pick_it_up",
            "cmd_strong_feet_strong_pace",
            "preview_elapsed",
        ]

        let missing = filenames.filter { bundledVoiceAudioURL(for: $0, bundle: .main) == nil }
        XCTAssertTrue(missing.isEmpty, "Missing male preview samples: \(missing)")
    }

    func testFemalePreviewCuesDoNotCrash() {
        let sut = makeVoiceCalloutService()

        sut.previewCommandCue(gender: .female)
        sut.previewCountdownCue(gender: .female)
    }

    func testGenderedVoiceFilenameUsesFemaleBundleSubdirectory() {
        XCTAssertEqual(
            genderedVoiceFilename("cmd_move_with_a_purpose", gender: .female),
            "female/cmd_move_with_a_purpose"
        )
        XCTAssertEqual(
            genderedVoiceFilename("female/cmd_move_with_a_purpose", gender: .female),
            "female/cmd_move_with_a_purpose"
        )
        XCTAssertEqual(
            genderedVoiceFilename("cmd_move_with_a_purpose", gender: .male),
            "cmd_move_with_a_purpose"
        )
    }

    func testApprovedVoiceFilenameRejectsUnapprovedMaleCatalogEntries() {
        XCTAssertEqual(
            approvedVoiceFilename("cmd_move_with_a_purpose", gender: .male),
            "cmd_move_with_a_purpose"
        )
        XCTAssertEqual(
            approvedVoiceFilename("cmd_chain_wrestling", gender: .male),
            "cmd_move_with_a_purpose"
        )
        // Female now also has an allowlist safety net
        XCTAssertEqual(
            approvedVoiceFilename("cmd_chain_wrestling", gender: .female),
            "female/cmd_move_with_a_purpose"
        )
        XCTAssertFalse(approvedMaleVoiceFilenames.contains("cmd_chain_wrestling"))
        XCTAssertFalse(approvedFemaleVoiceFilenames.contains("female/cmd_chain_wrestling"))
    }

    func testResetSessionAllowsElapsedMilestoneToReplay() {
        let sut = makeVoiceCalloutService()
        sut.triggerCallout(elapsedSeconds: 60)
        sut.resetSession()
        sut.triggerCallout(elapsedSeconds: 60)
    }

    func testResetSessionPreservesLastCommandCueToPreventImmediateSessionRepeat() {
        let sut = makeVoiceCalloutService()

        sut.beginSession(totalDurationSeconds: 300)
        sut.triggerCallout(elapsedSeconds: 30)
        let primed = sut._stateSnapshotForTesting()

        sut.resetSession()
        let reset = sut._stateSnapshotForTesting()

        XCTAssertNotNil(primed.lastCommandCueFilename)
        XCTAssertEqual(reset.lastCommandCueFilename, primed.lastCommandCueFilename)
        XCTAssertEqual(reset.lastElapsedMilestone, 0)
        XCTAssertEqual(reset.nextCommandCueAt, 0)
    }

    func testCommandCueScheduleDoesNotCrashAcrossLongRun() {
        let sut = makeVoiceCalloutService()
        for elapsed in 1...180 {
            sut.triggerCallout(elapsedSeconds: elapsed)
        }
    }

    func testCatalogHasVarietyAndClearElapsedLanguage() {
        let catalog = loadVoiceCalloutCatalog(bundle: .main)

        XCTAssertGreaterThanOrEqual(catalog.elapsedCues.count, 8)
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
                .init(second: 60, filename: "elapsed_primary", text: "Sixty elapsed."),
                .init(second: 60, filename: "elapsed_duplicate", text: "Sixty elapsed duplicate."),
            ],
            commandCues: [
                .init(filename: "cmd_primary", text: "Repeat me."),
                .init(filename: "cmd_duplicate", text: "Repeat me."),
            ]
        )

        XCTAssertEqual(catalog.elapsedCueBySecond[60]?.filename, "elapsed_primary")
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

    func testCommandCuePoolAvoidsRepeatedTextEvenWhenFilenameDiffers() {
        let cues = [
            VoiceCueCatalog.Cue(filename: "cue_a", text: "Move with a purpose."),
            VoiceCueCatalog.Cue(filename: "cue_b", text: "  Move with a purpose.  "),
            VoiceCueCatalog.Cue(filename: "cue_c", text: "Cut the angle and go."),
        ]

        let pool = commandCuePool(
            from: cues,
            usedFilenames: ["cue_a"],
            usedTexts: [normalizedVoiceCueText("Move with a purpose.")],
            lastFilename: "cue_a",
            lastText: "Move with a purpose."
        )

        XCTAssertEqual(pool.map(\.filename), ["cue_c"])
    }

    func testNextPreviewFilenameAvoidsImmediateRepeatWhenPossible() {
        var usedFilenames: Set<String> = ["cue_a"]

        let selected = nextPreviewFilename(
            from: ["cue_a", "cue_b", "cue_c"],
            lastFilename: "cue_b",
            usedFilenames: &usedFilenames
        ) { _ in 0 }

        XCTAssertEqual(selected, "cue_c")
        XCTAssertTrue(usedFilenames.contains("cue_c"))
    }

    func testTimersAtLeastThirtySecondsScheduleFirstCommandCueAtThirtySeconds() {
        XCTAssertEqual(initialFollowupCommandCueSecond(totalDurationSeconds: 12), .max)
        XCTAssertEqual(initialFollowupCommandCueSecond(totalDurationSeconds: 20), .max)
        XCTAssertEqual(initialFollowupCommandCueSecond(totalDurationSeconds: 30), .max)
        XCTAssertEqual(initialFollowupCommandCueSecond(totalDurationSeconds: 31), 30)
        XCTAssertEqual(initialFollowupCommandCueSecond(totalDurationSeconds: 40), 30)
    }

    func testVoiceNotificationPlanKeepsThirtySecondCadenceAndElapsedMilestones() {
        let catalog = VoiceCueCatalog(
            previewElapsed: .init(filename: "preview_elapsed", text: "Preview."),
            fallbackCommandFilename: "cmd_a",
            elapsedCues: [
                .init(second: 60, filename: "elapsed_60s", text: "One minute elapsed."),
                .init(second: 120, filename: "elapsed_120s", text: "Two minutes elapsed."),
            ],
            commandCues: [
                .init(filename: "cmd_a", text: "Command A."),
                .init(filename: "cmd_b", text: "Command B."),
                .init(filename: "cmd_c", text: "Command C."),
            ]
        )

        let plan = voiceCalloutNotificationPlan(
            totalDurationSeconds: 120,
            elapsedSeconds: 0,
            gender: .male,
            catalog: catalog,
            options: VoiceCalloutNotificationPlanOptions(
                audioExists: { _ in true },
                pickIndex: { _ in 0 }
            )
        )

        XCTAssertEqual(plan.map(\.offsetSeconds), [30, 60, 90, 120])
        XCTAssertEqual(plan[1].text, "One minute elapsed.")
        XCTAssertEqual(plan[3].text, "Two minutes elapsed.")
        XCTAssertTrue(zip(plan, plan.dropFirst()).allSatisfy { $1.offsetSeconds - $0.offsetSeconds >= 30 })
    }

    func testVoiceNotificationPlanAvoidsImmediateCommandRepeats() {
        let catalog = VoiceCueCatalog(
            previewElapsed: .init(filename: "preview_elapsed", text: "Preview."),
            fallbackCommandFilename: "cmd_a",
            elapsedCues: [],
            commandCues: [
                .init(filename: "cmd_a", text: "Command A."),
                .init(filename: "cmd_b", text: "Command B."),
            ]
        )

        let plan = voiceCalloutNotificationPlan(
            totalDurationSeconds: 90,
            elapsedSeconds: 0,
            gender: .male,
            catalog: catalog,
            options: VoiceCalloutNotificationPlanOptions(
                audioExists: { _ in true },
                pickIndex: { _ in 0 }
            )
        )

        XCTAssertEqual(plan.map(\.filename), ["cmd_a", "cmd_b", "cmd_a"])
    }

    func testPlaybackReactivatesAudioSessionAfterSessionBegin() {
        let counter = CounterBox()
        let sut = makeVoiceCalloutService(counter: counter)

        sut.beginSession(totalDurationSeconds: 60)
        sut.previewCountdownCue()

        XCTAssertGreaterThanOrEqual(
            counter.value,
            2,
            "Voice playback must reactivate AVAudioSession before cue playback."
        )
    }

    func testTimerCalloutsAlternateBetweenRandomCommandsAndConfiguredElapsedMarks() {
        let sut = makeVoiceCalloutService()

        sut.beginSession(totalDurationSeconds: 120)
        sut.triggerCallout(elapsedSeconds: 14)
        let beforeFirstCommand = sut._stateSnapshotForTesting()
        XCTAssertEqual(beforeFirstCommand.lastElapsedMilestone, 0)
        XCTAssertEqual(beforeFirstCommand.nextCommandCueAt, 30)
        XCTAssertNil(beforeFirstCommand.lastCommandCueFilename)

        sut.triggerCallout(elapsedSeconds: 30)
        let atThirty = sut._stateSnapshotForTesting()
        XCTAssertEqual(atThirty.lastElapsedMilestone, 0)
        XCTAssertEqual(atThirty.nextCommandCueAt, 60)
        XCTAssertNotNil(atThirty.lastCommandCueFilename)

        sut.triggerCallout(elapsedSeconds: 45)
        let atFortyFive = sut._stateSnapshotForTesting()
        XCTAssertEqual(atFortyFive.lastElapsedMilestone, 0)
        XCTAssertEqual(atFortyFive.nextCommandCueAt, 60)
        XCTAssertNotNil(atFortyFive.lastCommandCueFilename)

        sut.triggerCallout(elapsedSeconds: 60)
        let atSixty = sut._stateSnapshotForTesting()
        XCTAssertEqual(atSixty.lastElapsedMilestone, 60)
        XCTAssertEqual(atSixty.nextCommandCueAt, 90)
    }

    func testElapsedMinuteAnnouncementCatchesUpAfterSkippedSecond() {
        let sut = makeVoiceCalloutService()

        sut.beginSession(totalDurationSeconds: 180)
        sut.triggerCallout(elapsedSeconds: 61)

        let snapshot = sut._stateSnapshotForTesting()
        XCTAssertEqual(snapshot.lastElapsedMilestone, 60)
        XCTAssertEqual(snapshot.nextCommandCueAt, 91)
    }

    func testFirstTimedCalloutReactivatesAudioSessionBeforePlayback() {
        let counter = CounterBox()
        let sut = makeVoiceCalloutService(counter: counter)

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

    func testBackgroundVoiceKeepAliveIsNoopForAppReviewCompliance() {
        let engine = FakeBackgroundVoiceKeepAliveEngine()
        let activations = CounterBox()
        let deactivations = CounterBox()
        let sut = BackgroundVoiceKeepAliveService(
            makeEngine: { engine },
            activateAudioSession: { activations.value += 1 },
            deactivateAudioSession: { deactivations.value += 1 }
        )

        sut.start()
        sut.start()
        sut.stop()

        XCTAssertFalse(sut.isActive)
        XCTAssertEqual(activations.value, 0)
        XCTAssertEqual(engine.startCalls, 0)
        XCTAssertEqual(engine.attachedNodes, 0)
        XCTAssertEqual(engine.connectedNodes, 0)
        XCTAssertEqual(engine.prepareCalls, 0)
        XCTAssertEqual(deactivations.value, 0)
    }
}
