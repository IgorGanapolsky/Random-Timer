import StoreKit
import UIKit

@MainActor
final class StoreReviewManager {
    static let shared = StoreReviewManager()

    private let completionCountKey = "review_completion_count"
    private let lastReviewTimestampKey = "review_last_timestamp"
    private let lastReviewVersionKey = "review_last_version"

    private let completionsBeforeReview = 3
    private let minDaysBetweenRequests = 30

    private init() {}

    func recordCompletion() {
        let count = UserDefaults.standard.integer(forKey: completionCountKey) + 1
        UserDefaults.standard.set(count, forKey: completionCountKey)

        if isEligibleForReview() {
            requestReview()
        }
    }

    private func requestReview() {
        // Guard: only prompt when app is in the foreground with an active scene.
        // Avoids wasting one of the OS-enforced annual review request quota when
        // called from a background or notification path.
        guard let scene = try? currentWindowScene else { return }

        AnalyticsService.shared.track(AnalyticsEvents.reviewPromptRequested)
        // AppStore.requestReview shows the native prompt; the OS may suppress it.
        // We do NOT track writeReviewTapped here — the user has not tapped anything yet.
        AppStore.requestReview(in: scene)

        UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: lastReviewTimestampKey)
        UserDefaults.standard.set(appVersion, forKey: lastReviewVersionKey)
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
        let count = UserDefaults.standard.integer(forKey: completionCountKey)
        let lastTimestamp = UserDefaults.standard.double(forKey: lastReviewTimestampKey)
        let lastVersion = UserDefaults.standard.string(forKey: lastReviewVersionKey)

        guard count >= completionsBeforeReview else { return false }
        guard lastTimestamp != 0 else { return true }
        if lastVersion != appVersion { return true }

        let lastDate = Date(timeIntervalSince1970: lastTimestamp)
        let days = Calendar.current.dateComponents([.day], from: lastDate, to: Date()).day ?? 0
        return days >= minDaysBetweenRequests
    }

    private var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "unknown"
    }
}
