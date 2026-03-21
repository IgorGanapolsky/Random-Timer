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

    private func scrollUntilVisible(
        _ element: XCUIElement,
        in app: XCUIApplication,
        maxSwipes: Int = 4
    ) {
        for _ in 0..<maxSwipes where !element.exists {
            app.swipeUp()
        }
    }

    private func saveScreenshot(_ screenshot: XCUIScreenshot, named name: String, outputDir: String) {
        let path = "\(outputDir)/\(name)"
        FileManager.default.createFile(atPath: path, contents: screenshot.pngRepresentation)
    }

    func testSetupStateShowsStartTimer() {
        let app = launchApp()
        ensureSetupScreen(app)
    }

    func testSetupStateKeepsStartTimerHittable() {
        let app = launchApp()
        ensureSetupScreen(app)

        let startButton = app.buttons["Start Timer"]
        XCTAssertTrue(startButton.waitForExistence(timeout: 3.0))
        XCTAssertTrue(startButton.isHittable)
    }

    func testPreviewVoiceCueDoesNotCrashSetupScreen() {
        let app = launchApp()
        ensureSetupScreen(app)

        let previewButton = app.buttons["PREVIEW"]
        XCTAssertTrue(previewButton.waitForExistence(timeout: 3.0))
        previewButton.tap()

        let startButton = app.buttons["Start Timer"]
        XCTAssertTrue(
            startButton.waitForExistence(timeout: 3.0),
            "Preview must not crash the app or navigate away from setup."
        )
    }

    func testFreeRepeatLoopDetailsMatchAndroidCopy() {
        let app = launchApp()
        ensureSetupScreen(app)

        let loopToggle = app.switches["Loop Enabled"]
        scrollUntilVisible(loopToggle, in: app)
        XCTAssertTrue(loopToggle.waitForExistence(timeout: 3.0))

        if loopToggle.value as? String == "0" {
            loopToggle.tap()
        }

        XCTAssertTrue(app.staticTexts["Loop Mode"].waitForExistence(timeout: 2.0))
        XCTAssertTrue(
            app.staticTexts["Infinite Loop - Pro unlocks round limits"].waitForExistence(timeout: 2.0)
        )
    }

    func testProRepeatLoopDetailsMatchAndroidCopy() {
        let app = XCUIApplication()
        app.launchArguments += ["-ui-test-pro", "true"]
        app.launch()
        ensureSetupScreen(app)

        let loopToggle = app.switches["Loop Enabled"]
        scrollUntilVisible(loopToggle, in: app)
        XCTAssertTrue(loopToggle.waitForExistence(timeout: 3.0))

        if loopToggle.value as? String == "0" {
            loopToggle.tap()
        }

        let detailTitle = app.staticTexts["Round Selection"]
        let detailSummary = app.staticTexts["Infinite Rounds"]
        scrollUntilVisible(detailTitle, in: app)
        scrollUntilVisible(detailSummary, in: app)

        XCTAssertTrue(detailTitle.waitForExistence(timeout: 2.0))
        XCTAssertTrue(detailSummary.waitForExistence(timeout: 2.0))
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

    // MARK: - App Store Screenshot Capture

    func testCaptureAppStoreScreenshots() {
        let app = XCUIApplication()
        // The script expects raw screenshots in /tmp/appstore_screenshots
        let outputDir = "/tmp/appstore_screenshots"

        // Force Pro/Elite state for screenshots
        app.launchArguments += ["-ui-test-elite", "true"]

        addUIInterruptionMonitor(withDescription: "Notification Permission") { alert in
            let allowButton = alert.buttons["Allow"]
            if allowButton.exists { allowButton.tap(); return true }
            return false
        }

        // 1. Setup screen (with Round Selection visible)
        app.launch()
        // Toggle loop on to show round selection
        let loopToggle = app.switches["Loop Enabled"]
        if loopToggle.waitForExistence(timeout: 3.0) && loopToggle.value as? String == "0" {
            loopToggle.tap()
        }
        sleep(2)
        saveScreenshot(app.windows.firstMatch.screenshot(), named: "1_setup.png", outputDir: outputDir)

        // 2. Active timer (running state)
        let startButton = app.buttons["Start Timer"]
        XCTAssertTrue(startButton.waitForExistence(timeout: 3.0))
        startButton.tap()
        sleep(1)
        // Dismiss notification permission if it appears
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        sleep(2)
        saveScreenshot(app.windows.firstMatch.screenshot(), named: "2_active.png", outputDir: outputDir)

        // 3. Alarm state (timer just went off)
        app.terminate()
        app.launchArguments = ["-ui-test-state", "alarm", "-ui-test-pro", "true"]
        app.launch()
        sleep(2)
        saveScreenshot(app.windows.firstMatch.screenshot(), named: "3_alarm.png", outputDir: outputDir)

        // 4. Running timer (different view/state if needed)
        app.terminate()
        app.launchArguments = ["-ui-test-state", "running", "-ui-test-pro", "true"]
        app.launch()
        sleep(2)
        saveScreenshot(app.windows.firstMatch.screenshot(), named: "4_running.png", outputDir: outputDir)
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
