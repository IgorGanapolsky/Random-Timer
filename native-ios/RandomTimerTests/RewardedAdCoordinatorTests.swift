import XCTest
@testable import RandomTimer

@MainActor
private final class RecordingRewardedAdAnalytics: RewardedAdAnalyticsPort {
    struct TrackedEvent {
        let event: String
        let properties: [String: Any]?
    }

    private(set) var trackedEvents: [TrackedEvent] = []

    func track(_ event: String, properties: [String: Any]?) {
        trackedEvents.append(TrackedEvent(event: event, properties: properties))
    }
}

@MainActor
private final class RecordingRewardedAdPort: RewardedAdPort {
    var nextSuccess = false
    private(set) var showCount = 0

    func showRewardedAd(entryPoint: String, onFinished: @escaping (Bool) -> Void) {
        showCount += 1
        onFinished(nextSuccess)
    }
}

@MainActor
final class RewardedAdCoordinatorTests: XCTestCase {
    func testGrantsUnlockAndTracksWhenAdCompletes() {
        RewardedAdUnlockStore.consumeUnlock()
        let analytics = RecordingRewardedAdAnalytics()
        let port = RecordingRewardedAdPort()
        port.nextSuccess = true
        let coordinator = RewardedAdCoordinator(analytics: analytics, port: port)
        var unlocked = false

        coordinator.requestUnlock(
            entryPoint: RewardedAdPolicy.entryPointSoundArsenal,
            rewardedAdsEnabled: true,
            isPro: false,
            onUnlocked: { unlocked = true }
        )

        XCTAssertTrue(unlocked)
        XCTAssertTrue(RewardedAdUnlockStore.hasActiveUnlock())
        XCTAssertTrue(
            analytics.trackedEvents.contains(where: { $0.event == AnalyticsEvents.rewardedAdUnlock })
        )
    }

    func testDoesNotGrantWhenFlagDisabled() {
        RewardedAdUnlockStore.consumeUnlock()
        let analytics = RecordingRewardedAdAnalytics()
        let port = RecordingRewardedAdPort()
        let coordinator = RewardedAdCoordinator(analytics: analytics, port: port)

        coordinator.requestUnlock(
            entryPoint: RewardedAdPolicy.entryPointSoundArsenal,
            rewardedAdsEnabled: false,
            isPro: false,
            onUnlocked: {}
        )

        XCTAssertEqual(port.showCount, 0)
        XCTAssertFalse(RewardedAdUnlockStore.hasActiveUnlock())
    }
}
