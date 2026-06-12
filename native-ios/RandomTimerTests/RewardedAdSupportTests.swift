import XCTest
@testable import RandomTimer

final class RewardedAdSupportTests: XCTestCase {
    func testCanOfferWhenFlagEnabledAndNotPro() {
        XCTAssertTrue(RewardedAdPolicy.canOfferRewardedAd(rewardedAdsEnabled: true, isPro: false))
    }

    func testDoesNotOfferWhenFlagDisabled() {
        XCTAssertFalse(RewardedAdPolicy.canOfferRewardedAd(rewardedAdsEnabled: false, isPro: false))
    }

    func testDoesNotOfferForProUsers() {
        XCTAssertFalse(RewardedAdPolicy.canOfferRewardedAd(rewardedAdsEnabled: true, isPro: true))
    }

    func testAnalyticsEventNames() {
        XCTAssertEqual(RewardedAdAnalytics.requestedEvent, "rewarded_ad_requested")
        XCTAssertEqual(RewardedAdAnalytics.completedEvent, "rewarded_ad_completed")
        XCTAssertEqual(RewardedAdAnalytics.unlockEvent, "rewarded_ad_unlock")
    }

    func testResolvedRewardedUnitIdUsesTestIdInTestMode() {
        XCTAssertEqual(
            RewardedAdConfig.resolvedRewardedUnitId(useTestAds: true),
            RewardedAdConfig.testRewardedUnitIdIOS
        )
    }

    func testProductionIOSAdMobIdsRemainEmptyUntilConfigured() {
        XCTAssertEqual(RewardedAdConfig.productionAppIdIOS, "")
        XCTAssertEqual(RewardedAdConfig.productionRewardedUnitIdIOS, "")
    }

    func testResolvedRewardedUnitIdForDebugBuildUsesTestUnit() {
        #if DEBUG
        XCTAssertEqual(
            RewardedAdConfig.resolvedRewardedUnitIdForCurrentBuild(),
            RewardedAdConfig.testRewardedUnitIdIOS
        )
        #endif
    }

    func testEntryPointSoundArsenalMatchesAndroidContract() {
        XCTAssertEqual(RewardedAdPolicy.entryPointSoundArsenal, "sound_arsenal_gate")
    }
}
