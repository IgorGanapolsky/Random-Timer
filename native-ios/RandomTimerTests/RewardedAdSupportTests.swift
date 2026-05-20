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
}
