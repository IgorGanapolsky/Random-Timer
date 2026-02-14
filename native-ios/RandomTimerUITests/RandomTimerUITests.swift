import XCTest

@MainActor
final class RandomTimerUITests: XCTestCase {
    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    func testResetShowsRestartedFeedback() {
        let app = XCUIApplication()
        app.launch()

        let startButton = app.buttons["Start Timer"]
        if !startButton.waitForExistence(timeout: 2.0) {
            let stopButton = app.buttons["Stop"]
            if stopButton.waitForExistence(timeout: 2.0) {
                stopButton.tap()
            }
        }
        XCTAssertTrue(startButton.waitForExistence(timeout: 2.0))
        startButton.tap()

        let runningLabel = app.staticTexts["Timer running..."]
        XCTAssertTrue(runningLabel.waitForExistence(timeout: 2.0))

        let resetButton = app.buttons["Reset"]
        XCTAssertTrue(resetButton.waitForExistence(timeout: 2.0))
        resetButton.tap()

        let restartedLabel = app.staticTexts["Timer restarted"]
        XCTAssertTrue(restartedLabel.waitForExistence(timeout: 2.0))
    }

    func testTappingTimerCircleStopsWhenAlarmIsActive() {
        let app = XCUIApplication()
        app.launchArguments += ["-ui-test-state", "alarm"]
        app.launch()

        // CircularTimerView is labeled "Timer complete" for both ALARM and COMPLETE.
        let circle = app.otherElements["Timer complete"]
        if circle.waitForExistence(timeout: 2.0) {
            circle.tap()
        } else {
            let circleFallback = app.staticTexts["Timer complete"]
            XCTAssertTrue(circleFallback.waitForExistence(timeout: 2.0))
            circleFallback.tap()
        }

        // After dismiss, we should be back on the setup screen.
        XCTAssertTrue(app.buttons["Start Timer"].waitForExistence(timeout: 2.0))
    }
}
