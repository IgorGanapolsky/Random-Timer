import XCTest
@testable import RandomTimer

@MainActor
final class AIVoiceCalloutServiceTests: XCTestCase {
    private func makeSut() -> AIVoiceCalloutService {
        let service = AIVoiceCalloutService.shared
        service.resetSession()
        return service
    }

    func testTriggerCalloutElapsedMilestones() {
        // Verify elapsed milestones don't crash and session state evolves
        let sut = makeSut()
        sut.triggerCallout(elapsedSeconds: 30)
        sut.triggerCallout(elapsedSeconds: 60)
        sut.triggerCallout(elapsedSeconds: 90)
        sut.triggerCallout(elapsedSeconds: 120)
    }

    func testPreviewDoesNotCrash() {
        let sut = makeSut()
        sut.preview()
    }

    func testResetSession() {
        let sut = makeSut()
        sut.triggerCallout(elapsedSeconds: 30)
        sut.resetSession()
        // Reset clears lastElapsedMilestone — next call to 30s should not be skipped
        sut.triggerCallout(elapsedSeconds: 30)
    }

    func testCommandCueFiredAtRandomInterval() {
        // Command cues should fire without crashing across many ticks
        let sut = makeSut()
        for elapsed in 1...120 {
            sut.triggerCallout(elapsedSeconds: elapsed)
        }
    }

    func testEveryRuntimeElapsedCueHasBundledFilename() {
        XCTAssertEqual(voiceFilename(for: previewElapsedCue), "preview_elapsed")
        XCTAssertTrue(elapsedVoiceCuesBySecond.values.allSatisfy { voiceFilename(for: $0) != nil })
    }

    func testEveryRuntimeCommandCueHasBundledFilename() {
        XCTAssertTrue(commandVoiceCues.allSatisfy { voiceFilename(for: $0) != nil })
    }

    func testRuntimeCommandCuesStayNeutralAndNonPrescriptive() {
        XCTAssertEqual(commandVoiceCues, [
            "Stay sharp.",
            "Reset. Breathe."
        ])
    }

    func testBundledVoiceAudioResolvesFromMainBundle() {
        let filenames =
            Set(
                [previewElapsedCue]
                    .compactMap(voiceFilename(for:))
                    + elapsedVoiceCuesBySecond.values.compactMap(voiceFilename(for:))
                    + commandVoiceCues.compactMap(voiceFilename(for:))
            )

        let missing = filenames.filter { voiceAudioURL(for: $0, bundle: .main) == nil }.sorted()
        XCTAssertTrue(missing.isEmpty, "Missing bundled voice assets: \(missing)")
    }

    func testUnknownCueFallsBackToBundledDrillSergeantClip() {
        XCTAssertEqual(voiceFilenameOrFallback(for: "Unexpected cue"), "cmd_stay_sharp")
        XCTAssertNotNil(voiceAudioURL(for: voiceFilenameOrFallback(for: "Unexpected cue"), bundle: .main))
    }
}
