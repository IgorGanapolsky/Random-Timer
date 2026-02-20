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

    // MARK: - Screenshot Capture (run manually for App Store screenshots)

    func testCaptureScreenshots() {
        let app = XCUIApplication()
        let outputDir = "/tmp/appstore_screenshots"

        // Helper to dismiss system alerts (notification permission)
        addUIInterruptionMonitor(withDescription: "Notification Permission") { alert in
            let allowButton = alert.buttons["Allow"]
            if allowButton.exists {
                allowButton.tap()
                return true
            }
            return false
        }

        // 1. Setup screen
        app.launch()
        sleep(2)
        let setupScreenshot = app.windows.firstMatch.screenshot()
        let setupData = setupScreenshot.pngRepresentation
        FileManager.default.createFile(atPath: "\(outputDir)/1_setup.png", contents: setupData)

        // 2. Running timer — dismiss notification dialog first
        let startButton = app.buttons["Start Timer"]
        XCTAssertTrue(startButton.waitForExistence(timeout: 3.0))
        startButton.tap()
        sleep(1)
        // Tap anywhere to trigger the interruption monitor
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        sleep(1)
        // Handle alert manually if interruption monitor didn't catch it
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        let allowBtn = springboard.buttons["Allow"]
        if allowBtn.waitForExistence(timeout: 2.0) {
            allowBtn.tap()
        }
        sleep(2)
        let runningScreenshot = app.windows.firstMatch.screenshot()
        let runningData = runningScreenshot.pngRepresentation
        FileManager.default.createFile(atPath: "\(outputDir)/2_running.png", contents: runningData)

        // Stop the timer
        let stopButton = app.buttons["Stop"]
        if stopButton.waitForExistence(timeout: 2.0) {
            stopButton.tap()
        }
        sleep(1)

        // 3. Alarm state (timer just went off — shows Silence button)
        app.terminate()
        app.launchArguments = ["-ui-test-state", "alarm"]
        app.launch()
        sleep(2)
        let alarmScreenshot = app.windows.firstMatch.screenshot()
        let alarmData = alarmScreenshot.pngRepresentation
        FileManager.default.createFile(atPath: "\(outputDir)/3_alarm.png", contents: alarmData)
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

    func testStopReturnsToInteractiveSetupScreen() {
        let app = XCUIApplication()
        app.launch()

        let startButton = app.buttons["Start Timer"]
        XCTAssertTrue(startButton.waitForExistence(timeout: 2.0))
        XCTAssertTrue(startButton.isHittable)
        startButton.tap()

        let stopButton = app.buttons["Stop"]
        XCTAssertTrue(stopButton.waitForExistence(timeout: 2.0))
        XCTAssertTrue(stopButton.isHittable)
        stopButton.tap()

        let returnedStartButton = app.buttons["Start Timer"]
        XCTAssertTrue(returnedStartButton.waitForExistence(timeout: 2.0))
        XCTAssertTrue(returnedStartButton.isHittable)
        XCTAssertFalse(app.staticTexts["Timer running..."].exists)

        // Validate setup screen is fully interactive by starting again.
        returnedStartButton.tap()
        XCTAssertTrue(app.buttons["Stop"].waitForExistence(timeout: 2.0))
    }
}
