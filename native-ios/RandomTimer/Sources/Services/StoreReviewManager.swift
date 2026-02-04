import StoreKit
import Foundation

/// Manages in-app review prompts following Apple's guidelines
@MainActor
final class StoreReviewManager {
    static let shared = StoreReviewManager()

    private let completionCountKey = "timer_completion_count"
    private let lastReviewRequestKey = "last_review_request"
    private let completionsBeforeReview = 3
    private let minDaysBetweenRequests = 30

    private init() {}

    func onTimerCompleted() {
        let currentCount = UserDefaults.standard.integer(forKey: completionCountKey)
        UserDefaults.standard.set(currentCount + 1, forKey: completionCountKey)
    }

    func requestReviewIfAppropriate() {
        guard shouldRequestReview() else { return }

        // Request review - Apple controls whether it actually shows
        if let windowScene = UIApplication.shared.connectedScenes
            .first(where: { $0.activationState == .foregroundActive }) as? UIWindowScene {
            SKStoreReviewController.requestReview(in: windowScene)

            // Mark that we requested
            UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: lastReviewRequestKey)
        }
    }

    private func shouldRequestReview() -> Bool {
        let completionCount = UserDefaults.standard.integer(forKey: completionCountKey)
        let lastRequest = UserDefaults.standard.double(forKey: lastReviewRequestKey)

        let daysSinceLastRequest: Int
        if lastRequest == 0 {
            daysSinceLastRequest = Int.max
        } else {
            let lastRequestDate = Date(timeIntervalSince1970: lastRequest)
            daysSinceLastRequest = Calendar.current.dateComponents([.day], from: lastRequestDate, to: Date()).day ?? 0
        }

        return completionCount >= completionsBeforeReview &&
               (lastRequest == 0 || daysSinceLastRequest >= minDaysBetweenRequests)
    }

    var completionCount: Int {
        UserDefaults.standard.integer(forKey: completionCountKey)
    }
}
