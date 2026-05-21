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

    private func launchProApp() -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments += ["-ui-test-pro", "true"]
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
        let startButton = waitForPrimaryStartButton(in: app, timeout: timeout)
        if startButton != nil {
            return
        }

        let stopButton = app.buttons["Stop"]
        if stopButton.waitForExistence(timeout: 2.0) {
            stopButton.tap()
        }
        XCTAssertNotNil(waitForPrimaryStartButton(in: app, timeout: timeout))
    }

    private func primaryStartButton(in app: XCUIApplication) -> XCUIElement {
        let firstDrillButton = app.buttons["Start First Drill"]
        if firstDrillButton.exists {
            return firstDrillButton
        }
        return app.buttons["Start Timer"]
    }

    private func waitForPrimaryStartButton(
        in app: XCUIApplication,
        timeout: TimeInterval = 4.0
    ) -> XCUIElement? {
        let firstDrillButton = app.buttons["Start First Drill"]
        if firstDrillButton.waitForExistence(timeout: timeout) {
            return firstDrillButton
        }

        let startTimerButton = app.buttons["Start Timer"]
        if startTimerButton.waitForExistence(timeout: 0.5) {
            return startTimerButton
        }

        return nil
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

    private func scrollUntilVisible(
        _ element: XCUIElement,
        in app: XCUIApplication,
        maxSwipes: Int = 4
    ) {
        for _ in 0..<maxSwipes where !element.exists {
            app.swipeUp()
        }
    }

    func testSetupStateShowsStartTimer() {
        let app = launchApp()
        ensureSetupScreen(app)
    }

    func testSetupStateKeepsStartTimerHittable() {
        let app = launchApp()
        ensureSetupScreen(app)

        let startButton = primaryStartButton(in: app)
        XCTAssertTrue(startButton.waitForExistence(timeout: 3.0))
        XCTAssertTrue(startButton.isHittable)
    }

    func testPreviewVoiceCueDoesNotCrashSetupScreen() {
        let app = launchApp()
        ensureSetupScreen(app)

        let previewButton = app.buttons["PREVIEW"]
        XCTAssertTrue(previewButton.waitForExistence(timeout: 3.0))
        previewButton.tap()

        let startButton = primaryStartButton(in: app)
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
        let app = launchProApp()
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

    func testProSetupShowsVoiceCalloutsOffByDefault() {
        let app = launchProApp()
        ensureSetupScreen(app)

        let voiceToggle = app.switches["Voice Enabled"]
        scrollUntilVisible(voiceToggle, in: app)
        XCTAssertTrue(voiceToggle.waitForExistence(timeout: 3.0))
        XCTAssertEqual(voiceToggle.value as? String, "0")
    }

    func testRunningStateShowsRunningLabelAndPauseAction() {
        let app = launchApp(withState: "running")
        XCTAssertTrue(app.staticTexts["Timer running..."].waitForExistence(timeout: 2.0))
        XCTAssertTrue(app.buttons["Pause"].waitForExistence(timeout: 2.0))
        XCTAssertFalse(app.buttons["Start First Drill"].exists)
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
        XCTAssertFalse(app.buttons["Start First Drill"].exists)
        XCTAssertFalse(app.buttons["Start Timer"].exists)
    }

    func testResetShowsRestartedFeedback() {
        let app = launchApp()
        ensureSetupScreen(app)

        let startButton = primaryStartButton(in: app)
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
        XCTAssertFalse(app.buttons["Start First Drill"].exists)
        XCTAssertFalse(app.buttons["Start Timer"].exists)
    }

    // MARK: - App Store Screenshot Capture

    func testCaptureAppStoreScreenshots() {
        let app = XCUIApplication()
        let outputDir = ProcessInfo.processInfo.environment["APPSTORE_SCREENSHOT_OUTPUT_DIR"]
            ?? (NSTemporaryDirectory() as NSString).appendingPathComponent("appstore_screenshots")
        let isPadCapture = UIDevice.current.userInterfaceIdiom == .pad
        try? FileManager.default.createDirectory(atPath: outputDir, withIntermediateDirectories: true)

        // Force Pro/Elite state for screenshots
        app.launchArguments += ["-ui-test-elite", "true"]

        addUIInterruptionMonitor(withDescription: "Notification Permission") { alert in
            let allowButton = alert.buttons["Allow"]
            if allowButton.exists { allowButton.tap(); return true }
            return false
        }

        app.launch()
        captureSetupStorefront(app, isPadCapture: isPadCapture, outputDir: outputDir)
        captureSoundStorefrontIfNeeded(app, isPadCapture: isPadCapture, outputDir: outputDir)
        let startButton = primaryStartButton(in: app)
        XCTAssertTrue(startButton.waitForExistence(timeout: 3.0))
        startButton.tap()
        captureRunningStorefront(app, isPadCapture: isPadCapture, outputDir: outputDir)
        capturePausedStorefront(app, isPadCapture: isPadCapture, outputDir: outputDir)
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

private func saveScreenshot(_ screenshot: XCUIScreenshot, named name: String, outputDir: String) {
    let path = "\(outputDir)/\(name)"
    FileManager.default.createFile(atPath: path, contents: screenshot.pngRepresentation)
}

private func captureSetupStorefront(_ app: XCUIApplication, isPadCapture: Bool, outputDir: String) {
    let loopToggle = app.switches["Loop Enabled"]
    if loopToggle.waitForExistence(timeout: 3.0) && loopToggle.value as? String == "0" {
        loopToggle.tap()
    }
    sleep(2)
    saveScreenshot(
        app.windows.firstMatch.screenshot(),
        named: isPadCapture ? "5_ipad_setup.png" : "1_setup.png",
        outputDir: outputDir
    )
}

private func captureSoundStorefrontIfNeeded(_ app: XCUIApplication, isPadCapture: Bool, outputDir: String) {
    guard !isPadCapture else { return }

    app.swipeUp()
    sleep(1)
    saveScreenshot(
        app.windows.firstMatch.screenshot(),
        named: "3_alarm.png",
        outputDir: outputDir
    )
    app.swipeDown()
    sleep(1)
}

private func captureRunningStorefront(_ app: XCUIApplication, isPadCapture: Bool, outputDir: String) {
    sleep(1)
    app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
    sleep(2)
    saveScreenshot(
        app.windows.firstMatch.screenshot(),
        named: isPadCapture ? "6_ipad_running.png" : "2_active.png",
        outputDir: outputDir
    )
}

private func capturePausedStorefront(_ app: XCUIApplication, isPadCapture: Bool, outputDir: String) {
    let pauseButton = app.buttons["Pause"]
    if pauseButton.waitForExistence(timeout: 3.0) {
        pauseButton.tap()
    }
    sleep(2)
    saveScreenshot(
        app.windows.firstMatch.screenshot(),
        named: isPadCapture ? "7_ipad_stopped.png" : "4_running.png",
        outputDir: outputDir
    )
}
