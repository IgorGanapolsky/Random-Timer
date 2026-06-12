import Foundation

@MainActor
protocol RewardedAdAnalyticsPort: AnyObject {
    func track(_ event: String, properties: [String: Any]?)
}

extension AnalyticsService: RewardedAdAnalyticsPort {}

@MainActor
final class RewardedAdCoordinator {
    private let analytics: RewardedAdAnalyticsPort
    private let port: RewardedAdPort

    init(
        analytics: RewardedAdAnalyticsPort,
        port: RewardedAdPort = StubRewardedAdPort()
    ) {
        self.analytics = analytics
        self.port = port
    }

    func requestUnlock(
        entryPoint: String,
        rewardedAdsEnabled: Bool,
        isPro: Bool,
        onUnlocked: @escaping () -> Void
    ) {
        guard RewardedAdPolicy.canOfferRewardedAd(rewardedAdsEnabled: rewardedAdsEnabled, isPro: isPro) else {
            return
        }

        analytics.track(
            AnalyticsEvents.rewardedAdRequested,
            properties: RewardedAdAnalytics.requestedProperties(entryPoint: entryPoint)
        )
        port.showRewardedAd(entryPoint: entryPoint) { [analytics] success in
            analytics.track(
                AnalyticsEvents.rewardedAdCompleted,
                properties: RewardedAdAnalytics.completedProperties(entryPoint: entryPoint, success: success)
            )
            guard success else { return }

            RewardedAdUnlockStore.grantUnlock()
            analytics.track(
                AnalyticsEvents.rewardedAdUnlock,
                properties: RewardedAdAnalytics.unlockProperties(entryPoint: entryPoint)
            )
            onUnlocked()
        }
    }
}
