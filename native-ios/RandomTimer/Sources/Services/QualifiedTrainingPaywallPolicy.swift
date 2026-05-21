import Foundation

/// Action-triggered paywall aligned with WQTU (>=3 `timer_completed` in 7d).
/// Presents once after the user completes their third training session.
enum QualifiedTrainingPaywallPolicy {
    static let sessionThreshold = 3
    static let entryPoint = PaywallEntryPoint.qualifiedTrainingGate

    static func shouldPresent(
        completedSessionCount: Int,
        isPro: Bool,
        alreadyPresented: Bool
    ) -> Bool {
        !isPro && !alreadyPresented && completedSessionCount == sessionThreshold
    }
}

enum QualifiedTrainingPaywallAnalytics {
    static let eligibleEvent = "qualified_training_paywall_eligible"

    static func eligibleProperties(completedSessionCount: Int) -> [String: Any] {
        [
            AnalyticsProperties.entryPoint: QualifiedTrainingPaywallPolicy.entryPoint.rawValue,
            "completed_session_count": completedSessionCount,
            "monetization_phase": "p0_qualified_training_gate",
        ]
    }
}

enum QualifiedTrainingPaywallStore {
    private static let presentedKey = "qualified_training_paywall_presented"

    static func hasPresented() -> Bool {
        UserDefaults.standard.bool(forKey: presentedKey)
    }

    static func markPresented() {
        UserDefaults.standard.set(true, forKey: presentedKey)
    }
}
