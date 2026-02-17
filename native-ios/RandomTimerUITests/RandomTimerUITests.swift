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

    func testTappingTimerCircleSilencesAlarmAndStaysOnScreen() {
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

        // After tap, alarm silenced — user stays on timer screen with Stop/Reset buttons.
        XCTAssertTrue(app.buttons["Stop"].waitForExistence(timeout: 2.0))
        XCTAssertTrue(app.buttons["Reset"].waitForExistence(timeout: 2.0))
        // Should NOT navigate back to setup.
        XCTAssertFalse(app.buttons["Start Timer"].exists)
    }

    func testLandscapeShowsActionButtons() {
        let app = XCUIApplication()
        app.launchArguments += ["-ui-test-state", "alarm"]
        app.launch()

        let originalOrientation = XCUIDevice.shared.orientation
        defer { XCUIDevice.shared.orientation = originalOrientation }

        XCUIDevice.shared.orientation = .landscapeLeft

        let stopButton = app.buttons["Stop"]
        XCTAssertTrue(stopButton.waitForExistence(timeout: 2.0))
        XCTAssertTrue(stopButton.isHittable)
    }
}
