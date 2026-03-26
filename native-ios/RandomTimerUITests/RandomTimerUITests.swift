import XCTest

@MainActor
final class RandomTimerUITests: XCTestCase {
    private let appStoreScreenshotOutputDir = "/tmp/appstore_screenshots"

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    private func launchApp(withState state: String? = nil, extraLaunchArguments: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        if let state {
            app.launchArguments += ["-ui-test-state", state]
        }
        app.launchArguments += extraLaunchArguments
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

    private func launchScreenshotApp(withState state: String? = nil) -> XCUIApplication {
        launchApp(withState: state, extraLaunchArguments: ["-ui-test-elite", "true"])
    }

    private func captureAppStoreScreenshot(_ app: XCUIApplication, named name: String, delay: UInt32 = 2) {
        sleep(delay)
        let window = app.windows.firstMatch
        XCTAssertTrue(window.waitForExistence(timeout: 5.0), "Expected app window before capturing \(name)")
        saveScreenshot(window.screenshot(), named: name, outputDir: appStoreScreenshotOutputDir)
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

    func testFreeSetupShowsPreviewWithoutExtendedRangeToggle() {
        let app = launchApp()
        ensureSetupScreen(app)

        XCTAssertTrue(app.buttons["PREVIEW"].waitForExistence(timeout: 3.0))
        XCTAssertFalse(app.buttons["5m"].exists)
    }

    func testProSetupShowsExtendedRangeToggleAndHidesPreview() {
        let app = XCUIApplication()
        app.launchArguments += ["-ui-test-pro", "true"]
        app.launch()
        ensureSetupScreen(app)

        let rangeToggle = app.buttons["5m"]
        XCTAssertTrue(rangeToggle.waitForExistence(timeout: 3.0))
        XCTAssertFalse(app.buttons["PREVIEW"].exists)

        rangeToggle.tap()

        XCTAssertTrue(app.buttons["1H"].waitForExistence(timeout: 3.0))
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

    func testCaptureAppStorePhoneSetupScreenshot() {
        let app = launchScreenshotApp()
        let loopToggle = app.switches["Loop Enabled"]
        scrollUntilVisible(loopToggle, in: app)
        if loopToggle.waitForExistence(timeout: 3.0), loopToggle.value as? String == "0" {
            loopToggle.tap()
        }
        captureAppStoreScreenshot(app, named: "1_setup.png")
    }

    func testCaptureAppStorePhoneActiveScreenshot() {
        let app = launchScreenshotApp()
        ensureSetupScreen(app)
        let startButton = app.buttons["Start Timer"]
        XCTAssertTrue(startButton.waitForExistence(timeout: 3.0))
        startButton.tap()
        dismissSystemAlertsIfNeeded(app)
        captureAppStoreScreenshot(app, named: "2_active.png")
    }

    func testCaptureAppStorePhoneAlarmScreenshot() {
        let app = launchScreenshotApp(withState: "alarm")
        captureAppStoreScreenshot(app, named: "3_alarm.png")
    }

    func testCaptureAppStorePhoneRunningScreenshot() {
        let app = launchScreenshotApp(withState: "running")
        captureAppStoreScreenshot(app, named: "4_running.png")
    }

    func testCaptureAppStorePadSetupScreenshot() {
        let app = launchScreenshotApp()
        let loopToggle = app.switches["Loop Enabled"]
        scrollUntilVisible(loopToggle, in: app)
        if loopToggle.waitForExistence(timeout: 3.0), loopToggle.value as? String == "0" {
            loopToggle.tap()
        }
        captureAppStoreScreenshot(app, named: "5_ipad_setup.png")
    }

    func testCaptureAppStorePadRunningScreenshot() {
        let app = launchScreenshotApp(withState: "running")
        captureAppStoreScreenshot(app, named: "6_ipad_running.png")
    }

    func testCaptureAppStorePadStoppedScreenshot() {
        let app = launchScreenshotApp(withState: "complete")
        captureAppStoreScreenshot(app, named: "7_ipad_stopped.png")
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
