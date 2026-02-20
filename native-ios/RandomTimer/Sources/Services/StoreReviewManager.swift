import StoreKit
import UIKit

@MainActor
final class StoreReviewManager {
    static let shared = StoreReviewManager()

    private let qualifiedCompletionCountKey = "review_qualified_completion_count"
    private let totalCompletionCountKey = "review_total_completion_count"
    private let firstLaunchTimestampKey = "review_first_launch_timestamp"
    private let lastReviewTimestampKey = "review_last_timestamp"
    private let lastReviewVersionKey = "review_last_version"

    private let qualifiedCompletionsBeforeReview = 5
    private let minDaysBetweenRequests = 45
    private let minDaysSinceFirstLaunch = 3
    private let minimumSessionDurationForPrompt: TimeInterval = 45

    static let writeReviewURL = URL(string: "https://apps.apple.com/app/id6758355312?action=write-review")

    private init() {
        let defaults = UserDefaults.standard
        let firstLaunch = defaults.double(forKey: firstLaunchTimestampKey)
        if firstLaunch == 0 {
            defaults.set(Date().timeIntervalSince1970, forKey: firstLaunchTimestampKey)
        }
    }

    func recordCompletion(
        sessionDuration: TimeInterval,
        repeatEnabled: Bool,
        alarmSilenced: Bool
    ) {
        let defaults = UserDefaults.standard
        let total = defaults.integer(forKey: totalCompletionCountKey) + 1
        defaults.set(total, forKey: totalCompletionCountKey)

        guard isQualifiedCompletion(
            sessionDuration: sessionDuration,
            repeatEnabled: repeatEnabled,
            alarmSilenced: alarmSilenced
        ) else {
            return
        }

        let qualified = defaults.integer(forKey: qualifiedCompletionCountKey) + 1
        defaults.set(qualified, forKey: qualifiedCompletionCountKey)

        if isEligibleForReview() {
            requestReview()
        }
    }

    private func requestReview() {
        guard let scene = try? currentWindowScene else { return }

        try? AppStore.requestReview(in: scene)

        UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: lastReviewTimestampKey)
        UserDefaults.standard.set(appVersion, forKey: lastReviewVersionKey)
        UserDefaults.standard.set(0, forKey: qualifiedCompletionCountKey)
        AnalyticsService.shared.track(
            AnalyticsEvents.reviewPromptRequested,
            properties: [
                "app_version": appVersion,
                "qualified_completion_count": qualifiedCompletionsBeforeReview,
            ]
        )
    }

    private var currentWindowScene: UIWindowScene {
        get throws {
            guard let scene = UIApplication.shared.connectedScenes
                .first(where: { $0.activationState == .foregroundActive }) as? UIWindowScene else {
                throw StoreReviewError.noActiveScene
            }
            return scene
        }
    }

    private enum StoreReviewError: Error {
        case noActiveScene
    }

    private func isEligibleForReview() -> Bool {
        let defaults = UserDefaults.standard
        let qualifiedCount = defaults.integer(forKey: qualifiedCompletionCountKey)
        let lastTimestamp = defaults.double(forKey: lastReviewTimestampKey)
        let lastVersion = defaults.string(forKey: lastReviewVersionKey)
        let firstLaunchTimestamp = defaults.double(forKey: firstLaunchTimestampKey)

        guard qualifiedCount >= qualifiedCompletionsBeforeReview else { return false }
        guard hasReachedInstallAgeGate(firstLaunchTimestamp: firstLaunchTimestamp) else { return false }
        guard lastTimestamp != 0 else { return true }
        if lastVersion != appVersion { return true }

        let lastDate = Date(timeIntervalSince1970: lastTimestamp)
        let days = Calendar.current.dateComponents([.day], from: lastDate, to: Date()).day ?? 0
        return days >= minDaysBetweenRequests
    }

    private func hasReachedInstallAgeGate(firstLaunchTimestamp: TimeInterval) -> Bool {
        guard firstLaunchTimestamp > 0 else { return false }
        let firstLaunchDate = Date(timeIntervalSince1970: firstLaunchTimestamp)
        let days = Calendar.current.dateComponents([.day], from: firstLaunchDate, to: Date()).day ?? 0
        return days >= minDaysSinceFirstLaunch
    }

    private func isQualifiedCompletion(
        sessionDuration: TimeInterval,
        repeatEnabled: Bool,
        alarmSilenced: Bool
    ) -> Bool {
        guard sessionDuration >= minimumSessionDurationForPrompt else { return false }
        guard !repeatEnabled else { return false }
        guard !alarmSilenced else { return false }
        return true
    }

    private var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "unknown"
    }
}
