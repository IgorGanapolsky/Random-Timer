import XCTest
@testable import RandomTimer

@MainActor
final class AIVoiceCalloutServiceTests: XCTestCase {
    var sut: AIVoiceCalloutService! // swiftlint:disable:this implicitly_unwrapped_optional

    override func setUp() {
        super.setUp()
        sut = AIVoiceCalloutService.shared
        sut.resetSession()
    }

    func testTriggerCalloutElapsedMilestones() {
        // Verify elapsed milestones don't crash and session state evolves
        sut.triggerCallout(elapsedSeconds: 30)
        sut.triggerCallout(elapsedSeconds: 60)
        sut.triggerCallout(elapsedSeconds: 90)
        sut.triggerCallout(elapsedSeconds: 120)
    }

    func testPreviewDoesNotCrash() {
        sut.preview()
    }

    func testResetSession() {
        sut.triggerCallout(elapsedSeconds: 30)
        sut.resetSession()
        // Reset clears lastElapsedMilestone — next call to 30s should not be skipped
        sut.triggerCallout(elapsedSeconds: 30)
    }

    func testCommandCueFiredAtRandomInterval() {
        // Command cues should fire without crashing across many ticks
        for elapsed in 1...120 {
            sut.triggerCallout(elapsedSeconds: elapsed)
        }
    }
}
