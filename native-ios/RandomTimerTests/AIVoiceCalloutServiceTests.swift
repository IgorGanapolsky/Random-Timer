import XCTest
@testable import RandomTimer

@MainActor
final class AIVoiceCalloutServiceTests: XCTestCase {
    var sut: AIVoiceCalloutService!

    override func setUp() {
        super.setUp()
        sut = AIVoiceCalloutService.shared
        sut.resetSession()
    }

    func testTriggerCalloutFixedCountdown() {
        // This is tricky to test because it calls 'speak' which calls AVSpeechSynthesizer.
        // But we can at least verify it doesn't crash and session state evolves.
        sut.triggerCallout(remainingSeconds: 30)
        sut.triggerCallout(remainingSeconds: 10)
        sut.triggerCallout(remainingSeconds: 5)
    }

    func testPreviewCountdownCueDoesNotCrash() {
        sut.previewCountdownCue()
    }

    func testPreviewCommandCueDoesNotCrash() {
        sut.previewCommandCue()
    }

    func testResetSession() {
        sut.triggerCallout(remainingSeconds: 100)
        sut.resetSession()
        // verify internal state reset if possible via reflection or mock
    }
}
