import XCTest
@testable import RandomTimer

final class AppBootstrapTests: XCTestCase {
    func testHostedTestsSkipFirebaseAndAnalyticsEvenWhenConfigExists() {
        let plan = AppBootstrapPlan.resolve(
            skipHostedTests: true,
            hasBundledFirebaseConfig: true,
        )

        XCTAssertFalse(plan.shouldInitializeFirebase)
        XCTAssertFalse(plan.shouldInitializeAnalytics)
        XCTAssertEqual(plan.logMessage, "Skipping Firebase and analytics initialization for hosted tests.")
    }

    func testMissingFirebaseConfigSkipsFirebaseButKeepsAnalytics() {
        let plan = AppBootstrapPlan.resolve(
            skipHostedTests: false,
            hasBundledFirebaseConfig: false,
        )

        XCTAssertFalse(plan.shouldInitializeFirebase)
        XCTAssertTrue(plan.shouldInitializeAnalytics)
        XCTAssertEqual(
            plan.logMessage,
            "Skipping Firebase initialization because GoogleService-Info.plist is not bundled."
        )
    }

    func testBundledFirebaseConfigInitializesFullObservabilityStack() {
        let plan = AppBootstrapPlan.resolve(
            skipHostedTests: false,
            hasBundledFirebaseConfig: true,
        )

        XCTAssertTrue(plan.shouldInitializeFirebase)
        XCTAssertTrue(plan.shouldInitializeAnalytics)
        XCTAssertNil(plan.logMessage)
    }
}
