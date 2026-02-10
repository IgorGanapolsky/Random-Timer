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
}
