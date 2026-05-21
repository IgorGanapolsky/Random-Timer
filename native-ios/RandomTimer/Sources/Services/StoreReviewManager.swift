import StoreKit
import UIKit

func reviewPromptMilestone(for completionCount: Int) -> Int? {
    switch completionCount {
    case ..<3:
        return nil
    case 3..<10:
        return 3
    case 10..<25:
        return 10
    default:
        return 25 + ((completionCount - 25) / 25) * 25
    }
}

func isEligibleForReviewPrompt(
    completionCount: Int,
    lastPromptMilestone: Int,
    lastReviewTimestamp: TimeInterval,
    now: TimeInterval,
    minDaysBetweenRequests: Int
) -> Bool {
    guard let milestone = reviewPromptMilestone(for: completionCount) else { return false }
    guard milestone > lastPromptMilestone else { return false }
    guard lastReviewTimestamp != 0 else { return true }
    let elapsedDays = Int((now - lastReviewTimestamp) / 86_400)
    return elapsedDays >= minDaysBetweenRequests
}

@MainActor
final class StoreReviewManager {
    static let shared = StoreReviewManager()

    private let completionCountKey = "review_completion_count"
    private let lastReviewTimestampKey = "review_last_timestamp"
    private let lastReviewVersionKey = "review_last_version"
    private let pendingReviewKey = "review_pending_prompt"
    private let lastPromptMilestoneKey = "review_last_prompt_milestone"

    private let minDaysBetweenRequests = 30

    private init() {}

    /// Call when a training session is successfully completed (mirrors Android `recordCompletion`).
    /// Only queues a prompt; the UI calls `presentPendingReviewPromptIfQueued()` after returning
    /// to setup so the ask lands on a clear “win” surface (not mid-flow).
    func recordCompletion() {
        let count = UserDefaults.standard.integer(forKey: completionCountKey) + 1
        UserDefaults.standard.set(count, forKey: completionCountKey)

        if isEligibleToQueueReviewPrompt() {
            UserDefaults.standard.set(true, forKey: pendingReviewKey)
        }
    }

    /// Present the in-app review UI only when a completion queued a prompt (parity with Android).
    func presentPendingReviewPromptIfQueued() {
        guard UserDefaults.standard.bool(forKey: pendingReviewKey) else { return }
        UserDefaults.standard.set(false, forKey: pendingReviewKey)

        guard let scene = try? currentWindowScene else { return }

        AnalyticsService.shared.track(AnalyticsEvents.reviewPromptRequested)
        AppStore.requestReview(in: scene)

        UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: lastReviewTimestampKey)
        UserDefaults.standard.set(appVersion, forKey: lastReviewVersionKey)
        UserDefaults.standard.set(
            reviewPromptMilestone(for: UserDefaults.standard.integer(forKey: completionCountKey)) ?? 0,
            forKey: lastPromptMilestoneKey
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

    private func isEligibleToQueueReviewPrompt() -> Bool {
        let count = UserDefaults.standard.integer(forKey: completionCountKey)
        let lastTimestamp = UserDefaults.standard.double(forKey: lastReviewTimestampKey)
        let lastPromptMilestone = UserDefaults.standard.integer(forKey: lastPromptMilestoneKey)
        return isEligibleForReviewPrompt(
            completionCount: count,
            lastPromptMilestone: lastPromptMilestone,
            lastReviewTimestamp: lastTimestamp,
            now: Date().timeIntervalSince1970,
            minDaysBetweenRequests: minDaysBetweenRequests
        )
    }

    private var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "unknown"
    }
}
