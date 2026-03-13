import XCTest

@MainActor
final class RandomTimerUITests: XCTestCase {
    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    private func launchApp(withState state: String? = nil) -> XCUIApplication {
        let app = XCUIApplication()
        if let state {
            app.launchArguments += ["-ui-test-state", state]
        }
        app.launch()
        dismissSystemAlertsIfNeeded(app)
        return app
    }

    private func dismissSystemAlertsIfNeeded(_ app: XCUIApplication) {
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        let allowButton = springboard.buttons["Allow"]
        if allowButton.waitForExistence(timeout: 1.5) {
            allowButton.tap()
        }
    }

    private func ensureSetupScreen(_ app: XCUIApplication, timeout: TimeInterval = 4.0) {
        let startButton = app.buttons["Start Timer"]
        if startButton.waitForExistence(timeout: timeout) {
            return
        }

        let stopButton = app.buttons["Stop"]
        if stopButton.waitForExistence(timeout: 2.0) {
            stopButton.tap()
        }
        XCTAssertTrue(startButton.waitForExistence(timeout: timeout))
    }

    func testSetupStateShowsStartTimer() {
        let app = launchApp()
        ensureSetupScreen(app)
    }

    func testRunningStateShowsRunningLabelAndPauseAction() {
        let app = launchApp(withState: "running")
        XCTAssertTrue(app.staticTexts["Timer running..."].waitForExistence(timeout: 2.0))
        XCTAssertTrue(app.buttons["Pause"].waitForExistence(timeout: 2.0))
        XCTAssertFalse(app.buttons["Start Timer"].exists)
    }

    func testPausedStateShowsPausedLabelAndResumeAction() {
        let app = launchApp(withState: "paused")
        XCTAssertTrue(app.staticTexts["Paused"].waitForExistence(timeout: 2.0))
        XCTAssertTrue(app.buttons["Resume"].waitForExistence(timeout: 2.0))
        XCTAssertTrue(app.staticTexts["You don't know when it will go off..."].waitForExistence(timeout: 2.0))
    }

    func testAlarmStateShowsStopAndResetActions() {
        var app = launchApp(withState: "alarm")
        if !app.buttons["Stop"].waitForExistence(timeout: 8.0) {
            app.terminate()
            app = launchApp(withState: "alarm")
        }
        XCTAssertTrue(app.buttons["Stop"].waitForExistence(timeout: 8.0))
        XCTAssertTrue(app.buttons["Reset"].waitForExistence(timeout: 8.0))
        XCTAssertFalse(app.buttons["Start Timer"].exists)
    }

    func testResetShowsRestartedFeedback() {
        let app = launchApp()
        ensureSetupScreen(app)

        let startButton = app.buttons["Start Timer"]
        XCTAssertTrue(startButton.waitForExistence(timeout: 3.0))
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

        let stopButton = app.buttons["Stop"]
        XCTAssertTrue(stopButton.waitForExistence(timeout: 5.0), "Expected alarm seed to show active timer controls")

        // Tap center screen (same as user tapping timer circle area in alarm mode).
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()

        // After tap, alarm silenced — user stays on timer screen with Stop/Reset buttons.
        XCTAssertTrue(stopButton.waitForExistence(timeout: 2.0))
        XCTAssertTrue(app.buttons["Reset"].waitForExistence(timeout: 2.0))
        // Should NOT navigate back to setup.
        XCTAssertFalse(app.buttons["Start Timer"].exists)
    }

    // MARK: - Screenshot Capture (run manually for App Store screenshots)

    func testCaptureScreenshots() {
        let app = XCUIApplication()
        let outputDir = "/tmp/appstore_screenshots"

        addUIInterruptionMonitor(withDescription: "Notification Permission") { alert in
            let allowButton = alert.buttons["Allow"]
            if allowButton.exists { allowButton.tap(); return true }
            return false
        }

        // 1. Setup screen
        app.launch()
        sleep(2)
        let setupScreenshot = app.windows.firstMatch.screenshot()
        let setupData = setupScreenshot.pngRepresentation
        FileManager.default.createFile(atPath: "\(outputDir)/1_setup.png", contents: setupData)

        // 2. Running timer
        let startButton = app.buttons["Start Timer"]
        if !startButton.waitForExistence(timeout: 3.0) {
            let stopButton = app.buttons["Stop"]
            if stopButton.waitForExistence(timeout: 2.0) { stopButton.tap() }
        }
        XCTAssertTrue(startButton.waitForExistence(timeout: 3.0))
        startButton.tap()
        sleep(1)
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        sleep(1)
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        let allowBtn = springboard.buttons["Allow"]
        if allowBtn.waitForExistence(timeout: 2.0) { allowBtn.tap() }
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

        // 4. Paused state
        app.terminate()
        app.launchArguments = ["-ui-test-state", "paused"]
        app.launch()
        sleep(2)
        let pausedScreenshot = app.windows.firstMatch.screenshot()
        let pausedData = pausedScreenshot.pngRepresentation
        FileManager.default.createFile(atPath: "\(outputDir)/5_paused.png", contents: pausedData)
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
