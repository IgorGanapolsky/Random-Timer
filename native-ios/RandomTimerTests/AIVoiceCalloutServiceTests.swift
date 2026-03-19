import XCTest
@testable import RandomTimer

@MainActor
final class AIVoiceCalloutServiceTests: XCTestCase {
    private func makeSut() -> AIVoiceCalloutService {
        let service = AIVoiceCalloutService.shared
        service.resetSession()
        return service
    }

    func testTriggerCalloutElapsedMilestonesDoNotCrash() {
        let sut = makeSut()
        [30, 60, 90, 120, 180, 300, 600].forEach { elapsed in
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
        for elapsed in 1...120 {
            sut.triggerCallout(elapsedSeconds: elapsed)
        }
    }

    func testEveryRuntimeElapsedCueHasBundledFilename() {
        XCTAssertEqual(voiceFilename(for: previewElapsedCue), "preview_elapsed")
        XCTAssertTrue(elapsedVoiceCuesBySecond.values.allSatisfy { voiceFilename(for: $0) != nil })
    }

    func testEveryRuntimeCommandCueHasBundledFilename() {
        XCTAssertFalse(commandVoiceCues.isEmpty)
        XCTAssertTrue(commandVoiceCues.allSatisfy { voiceFilename(for: $0) != nil })
    }

    func testBundledVoiceAudioResolvesFromMainBundle() {
        let filenames = Set(
            [previewElapsedCue]
                .compactMap(voiceFilename(for:))
                + elapsedVoiceCuesBySecond.values.compactMap(voiceFilename(for:))
                + commandVoiceCues.compactMap(voiceFilename(for:))
        )

        let missing = filenames.filter { voiceAudioURL(for: $0, bundle: .main) == nil }.sorted()
        XCTAssertTrue(missing.isEmpty, "Missing bundled voice assets: \(missing)")
    }

    func testUnknownCueFallsBackToBundledDrillSergeantClip() {
        let fallback = voiceFilenameOrFallback(for: "Unexpected cue")
        XCTAssertEqual(fallback, "cmd_stay_sharp")
        XCTAssertNotNil(voiceAudioURL(for: fallback, bundle: .main))
    }
}
