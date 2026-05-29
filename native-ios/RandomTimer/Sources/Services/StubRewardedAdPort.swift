import Foundation

/// Rewarded ad port. [StubRewardedAdPort] is the default until AdMob SDK + publisher account ship.
@MainActor
protocol RewardedAdPort {
    func showRewardedAd(entryPoint: String, onFinished: @escaping (Bool) -> Void)
}

/// No-op until AdMob SDK is integrated (flag stays off in production).
@MainActor
struct StubRewardedAdPort: RewardedAdPort {
    func showRewardedAd(entryPoint: String, onFinished: @escaping (Bool) -> Void) {
        onFinished(false)
    }
}
