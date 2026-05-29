import Foundation

enum RewardedAdConfig {
    static let featureFlagKey = PostHogExperimentKeys.rewardedAdsEnabled
    static let testRewardedUnitIdIOS = "ca-app-pub-3940256099942544/1712485313"
    static let publisherId = "pub-5173650670360699"
    /// Production AdMob app ID (iOS). Empty until App Store app is linked in AdMob console.
    static let productionAppIdIOS = ""
    /// Production rewarded unit (iOS). Empty until ad unit is created in AdMob console.
    static let productionRewardedUnitIdIOS = ""
    static let admobBlocker =
        "Rewarded ads ship behind PostHog flag (default off) until production ad unit IDs are configured and app-ads.txt verifies."

    static func resolvedRewardedUnitId(useTestAds: Bool) -> String {
        useTestAds ? testRewardedUnitIdIOS : productionRewardedUnitIdIOS
    }

    static func resolvedRewardedUnitIdForCurrentBuild() -> String {
        #if DEBUG
        return testRewardedUnitIdIOS
        #else
        return resolvedRewardedUnitId(useTestAds: false)
        #endif
    }
}

enum RewardedAdPolicy {
    static let unlockFeature = "pro_sound_trial"
    static let entryPointSoundArsenal = "sound_arsenal_gate"

    static func canOfferRewardedAd(rewardedAdsEnabled: Bool, isPro: Bool) -> Bool {
        rewardedAdsEnabled && !isPro
    }
}

enum RewardedAdAnalytics {
    static let requestedEvent = "rewarded_ad_requested"
    static let completedEvent = "rewarded_ad_completed"
    static let unlockEvent = "rewarded_ad_unlock"

    static func requestedProperties(entryPoint: String) -> [String: Any] {
        baseProperties(entryPoint: entryPoint)
    }

    static func completedProperties(entryPoint: String, success: Bool) -> [String: Any] {
        var props = baseProperties(entryPoint: entryPoint)
        props[AnalyticsProperties.success] = success
        return props
    }

    static func unlockProperties(entryPoint: String) -> [String: Any] {
        baseProperties(entryPoint: entryPoint)
    }

    private static func baseProperties(entryPoint: String) -> [String: Any] {
        [
            AnalyticsProperties.entryPoint: entryPoint,
            "unlock_feature": RewardedAdPolicy.unlockFeature,
            "monetization_phase": "p1_rewarded_ads",
            "admob_blocker": RewardedAdConfig.admobBlocker,
        ]
    }
}

enum RewardedAdUnlockStore {
    private static let activeKey = "rewarded_ad_pro_sound_trial_active"

    static func hasActiveUnlock() -> Bool {
        UserDefaults.standard.bool(forKey: activeKey)
    }

    static func grantUnlock() {
        UserDefaults.standard.set(true, forKey: activeKey)
    }

    static func consumeUnlock() {
        UserDefaults.standard.set(false, forKey: activeKey)
    }
}
