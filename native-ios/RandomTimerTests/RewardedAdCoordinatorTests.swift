import XCTest
@testable import RandomTimer

@MainActor
final class RewardedAdCoordinatorTests: XCTestCase {
    private var analytics: RecordingRewardedAdAnalytics!
    private var port: RecordingRewardedAdPort!
    private var coordinator: RewardedAdCoordinator!

    override func setUp() {
        super.setUp()
        analytics = RecordingRewardedAdAnalytics()
        port = RecordingRewardedAdPort()
        coordinator = RewardedAdCoordinator(analytics: analytics, port: port)
        RewardedAdUnlockStore.consumeUnlock()
    }

    func testGrantsUnlockAndTracksWhenAdCompletes() {
        var unlocked = false
        port.nextSuccess = true

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
        coordinator.requestUnlock(
            entryPoint: RewardedAdPolicy.entryPointSoundArsenal,
            rewardedAdsEnabled: false,
            isPro: false,
            onUnlocked: {}
        )

        XCTAssertEqual(port.showCount, 0)
        XCTAssertFalse(RewardedAdUnlockStore.hasActiveUnlock())
    }

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

    private final class RecordingRewardedAdPort: RewardedAdPort {
        var nextSuccess = false
        private(set) var showCount = 0

        func showRewardedAd(entryPoint: String, onFinished: @escaping (Bool) -> Void) {
            showCount += 1
            onFinished(nextSuccess)
        }
    }
}
