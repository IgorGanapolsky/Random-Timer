import XCTest
@testable import RandomTimer

@MainActor
final class AIVoiceCalloutServiceTests: XCTestCase {
    func testRuntimeVoiceCueUsesCommandCueAtElapsedMilestone() {
        XCTAssertEqual(runtimeVoiceCue(for: 60, lastElapsedMilestone: 0), "Move now.")
    }

    func testRuntimeVoiceCueSuppressesDuplicateElapsedMilestone() {
        XCTAssertNil(runtimeVoiceCue(for: 120, lastElapsedMilestone: 120))
    }

    func testVoiceFilenameMapsRuntimeCueToBundledCommandAsset() {
        XCTAssertEqual(voiceFilename(for: "Drive forward."), "cmd_drive_forward")
    }

    func testVoiceFilenameFallsBackToBundledCommandAsset() {
        XCTAssertEqual(voiceFilenameOrFallback(for: "Unexpected cue"), "cmd_stay_sharp")
    }

    func testBundledCommandVoiceAudioResolvesFromMainBundle() {
        XCTAssertNotNil(voiceAudioURL(for: "cmd_stay_sharp", bundle: .main))
    }
}
