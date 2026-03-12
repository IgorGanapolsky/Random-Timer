import XCTest

@MainActor
final class RandomTimerUITests: XCTestCase {
    private enum ScreenshotDeviceClass: String {
        case iphone
        case ipad
    }

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
        // Tap near the top-left corner to avoid hitting the central Timer Circle
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.1, dy: 0.1)).tap()
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

    private func waitForScreen(_ identifier: String, timeout: TimeInterval = 10.0) {
        let screen = XCUIApplication().otherElements[identifier]
        XCTAssertTrue(screen.waitForExistence(timeout: timeout), "Screen \(identifier) should appear")
    }

    private func screenshotDeviceClass(for app: XCUIApplication) -> ScreenshotDeviceClass {
        let width = app.windows.firstMatch.frame.width
        return width >= 700 ? .ipad : .iphone
    }

    private func capture(_ app: XCUIApplication, named filename: String, outputDir: String) {
        let screenshot = app.windows.firstMatch.screenshot()
        let path = "\(outputDir)/\(filename)"
        let data = screenshot.pngRepresentation
        _ = FileManager.default.createFile(atPath: path, contents: data)
    }

    func testRunningStateShowsRunningLabelAndPauseAction() {
        let app = launchApp(withState: "running")

        waitForScreen("activeTimerScreen")

        let pauseButton = app.buttons["Pause"]
        XCTAssertTrue(pauseButton.waitForExistence(timeout: 7.0), "Pause button should appear in running state")

        let statusText = app.staticTexts["Timer running..."]
        XCTAssertTrue(statusText.waitForExistence(timeout: 5.0), "Timer running status should be visible")

        XCTAssertFalse(app.buttons["Start Timer"].exists, "Setup screen should not be visible")
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

    func testTappingTimerCircleStopsAlarmAndGoesHome() {
        let app = XCUIApplication()
        app.launchArguments += ["-ui-test-state", "alarm"]
        app.launch()

        let stopButton = app.buttons["Stop"]
        XCTAssertTrue(stopButton.waitForExistence(timeout: 5.0), "Expected alarm seed to show active timer controls")

        // Tap center screen (same as user tapping timer circle area in alarm mode).
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()

        // After tap, alarm should be stopped and we should be back on the setup screen.
        let startButton = app.buttons["Start Timer"]
        XCTAssertTrue(startButton.waitForExistence(timeout: 5.0), "Should navigate back to setup screen after tapping timer circle")
    }

    func testTappingTimerCircleInCompleteStateGoesHome() {
        let app = XCUIApplication()
        app.launchArguments += ["-ui-test-state", "complete"]
        app.launch()

        let stopButton = app.buttons["Stop"]
        XCTAssertTrue(stopButton.waitForExistence(timeout: 5.0), "Expected complete seed to show active timer controls")

        // Tap center screen (same as user tapping timer circle area in complete mode).
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()

        // After tap, should be back on the setup screen.
        let startButton = app.buttons["Start Timer"]
        XCTAssertTrue(
            startButton.waitForExistence(timeout: 5.0),
            "Should navigate back to setup screen after tapping timer circle in complete state"
        )
    }

    // MARK: - Screenshot Capture (manual App Store asset generation)

    func testCaptureAppStoreScreenshots() throws {
        let outputDir = "/tmp/appstore_screenshots"

        try FileManager.default.createDirectory(
            atPath: outputDir,
            withIntermediateDirectories: true,
            attributes: nil
        )

        addUIInterruptionMonitor(withDescription: "Notification Permission") { alert in
            let allowButton = alert.buttons["Allow"]
            if allowButton.exists {
                allowButton.tap()
                return true
            }
            return false
        }

        var app = launchApp()
        ensureSetupScreen(app)
        dismissSystemAlertsIfNeeded(app)
        let deviceClass = screenshotDeviceClass(for: app)

        switch deviceClass {
        case .iphone:
            capture(app, named: "iphone_setup_raw.png", outputDir: outputDir)

            app.swipeUp()
            capture(app, named: "iphone_sound_raw.png", outputDir: outputDir)
            app.swipeDown()

            let startButton = app.buttons["Start Timer"]
            XCTAssertTrue(startButton.waitForExistence(timeout: 3.0))
            startButton.tap()
            app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
            let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
            let allowButton = springboard.buttons["Allow"]
            if allowButton.waitForExistence(timeout: 2.0) {
                allowButton.tap()
            }
            let pauseButton = app.buttons["Pause"]
            XCTAssertTrue(pauseButton.waitForExistence(timeout: 5.0))
            capture(app, named: "iphone_running_raw.png", outputDir: outputDir)

            pauseButton.tap()
            XCTAssertTrue(app.staticTexts["Paused"].waitForExistence(timeout: 5.0))
            capture(app, named: "iphone_paused_raw.png", outputDir: outputDir)

        case .ipad:
            capture(app, named: "ipad_setup_raw.png", outputDir: outputDir)

            app.swipeUp()
            capture(app, named: "ipad_sound_raw.png", outputDir: outputDir)
            app.swipeDown()

            let startButton = app.buttons["Start Timer"]
            XCTAssertTrue(startButton.waitForExistence(timeout: 3.0))
            startButton.tap()
            app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
            let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
            let allowButton = springboard.buttons["Allow"]
            if allowButton.waitForExistence(timeout: 2.0) {
                allowButton.tap()
            }
            let pauseButton = app.buttons["Pause"]
            XCTAssertTrue(pauseButton.waitForExistence(timeout: 5.0))
            capture(app, named: "ipad_running_raw.png", outputDir: outputDir)
        }
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
