import XCTest
@testable import RandomTimer

@MainActor
final class AIVoiceCalloutServiceTests: XCTestCase {
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
            .filter { voiceAudioURL(for: $0, bundle: .main) == nil }
            .sorted()

        XCTAssertTrue(missing.isEmpty, "Missing bundled voice assets: \(missing)")
    }

    func testUnknownCueFallsBackToBundledDrillInstructorClip() {
        let catalog = loadVoiceCalloutCatalog(bundle: .main)
        let fallback = voiceFilenameOrFallback(for: "Unexpected cue", bundle: .main)

        XCTAssertEqual(fallback, catalog.fallbackCommandCue.filename)
        XCTAssertNotNil(voiceAudioURL(for: fallback, bundle: .main))
    }

    func testNextCommandCueAvoidsImmediateRepeatWhenPossible() {
        let cues = [
            VoiceCueCatalog.Cue(filename: "cue_a", text: "Cue A"),
            VoiceCueCatalog.Cue(filename: "cue_b", text: "Cue B"),
        ]

        let selected = nextCommandCue(from: cues, lastFilename: "cue_a") { _ in 0 }
        XCTAssertEqual(selected.filename, "cue_b")
    }
}
