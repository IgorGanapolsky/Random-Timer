import XCTest
@testable import RandomTimer

final class QualifiedTrainingPaywallPolicyTests: XCTestCase {
    func testDoesNotPresentBeforeThirdSession() {
        XCTAssertFalse(
            QualifiedTrainingPaywallPolicy.shouldPresent(
                completedSessionCount: 2,
                isPro: false,
                alreadyPresented: false
            )
        )
    }

    func testPresentsAfterThirdSessionForFreeUsers() {
        XCTAssertTrue(
            QualifiedTrainingPaywallPolicy.shouldPresent(
                completedSessionCount: 3,
                isPro: false,
                alreadyPresented: false
            )
        )
    }

    func testDoesNotPresentForProUsers() {
        XCTAssertFalse(
            QualifiedTrainingPaywallPolicy.shouldPresent(
                completedSessionCount: 3,
                isPro: true,
                alreadyPresented: false
            )
        )
    }

    func testDoesNotPresentWhenAlreadyShown() {
        XCTAssertFalse(
            QualifiedTrainingPaywallPolicy.shouldPresent(
                completedSessionCount: 3,
                isPro: false,
                alreadyPresented: true
            )
        )
    }

    func testDoesNotRePresentOnFourthSession() {
        XCTAssertFalse(
            QualifiedTrainingPaywallPolicy.shouldPresent(
                completedSessionCount: 4,
                isPro: false,
                alreadyPresented: false
            )
        )
    }

    func testEligibleAnalyticsEventMatchesAndroidContract() {
        XCTAssertEqual(
            QualifiedTrainingPaywallAnalytics.eligibleEvent,
            "qualified_training_paywall_eligible"
        )
        let properties = QualifiedTrainingPaywallAnalytics.eligibleProperties(completedSessionCount: 3)
        XCTAssertEqual(properties[AnalyticsProperties.entryPoint] as? String, "qualified_training_gate")
        XCTAssertEqual(properties["completed_session_count"] as? Int, 3)
        XCTAssertEqual(properties["monetization_phase"] as? String, "p0_qualified_training_gate")
    }
}
