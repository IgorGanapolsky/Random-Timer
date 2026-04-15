import XCTest
@testable import RandomTimer

final class TimerConfigProClampingTests: XCTestCase {
    @MainActor
    func testPaywallHiddenUnlockHoldDurationIsEightSeconds() {
        XCTAssertEqual(PaywallSheet.hiddenUnlockHoldDuration, 8.0, accuracy: 0.001)
    }

    @MainActor
    func testPaywallCopyFocusesOnTrainingOutcomes() {
        XCTAssertEqual(PaywallSheet.headline, "Stop Training With the Brakes On")
        XCTAssertEqual(
            PaywallSheet.subheadline,
            "Go unlimited — sessions up to 60 minutes, live voice callouts, "
                + "and a full sound library built for pressure drills."
        )
        let expectedFooter =
            "Cancel anytime. Subscription auto-renews until cancelled. "
            + "Price shown on Apple's confirmation sheet."
        XCTAssertEqual(PaywallSheet.subscriptionFooter, expectedFooter)
        XCTAssertEqual(
            PaywallSheet.featureRows,
            [
                "Full-length sessions — up to 60 minutes, no cutoffs",
                "Live voice callouts keep you sharp under pressure",
                "Loop drills with round limits — just like competition",
                "Full sound arsenal — real bells, horns, and sirens",
                "Verified audio drops when new packs are ready",
            ]
        )
    }

    func testPaywallExperimentVariantLabelsMatchAndroid() {
        XCTAssertEqual(PaywallExperimentVariants.label(defaultAnnual: false), "monthly_default")
        XCTAssertEqual(PaywallExperimentVariants.label(defaultAnnual: true), "annual_default")
        XCTAssertEqual(PostHogExperimentKeys.paywallDefaultPlanAnnual, "paywall_default_plan_annual")
        XCTAssertEqual(PostHogExperimentKeys.paywallValueFraming, "paywall_value_framing")
    }

    @MainActor
    func testPaywallOutcomesFirstHeadlineMatchesAndroidExperimentCopy() {
        XCTAssertEqual(PaywallSheet.headlineOutcomesFirst, "Finish Strong When the Clock Attacks")
    }

    func testPaywallUsesApprovedAppStoreConnectProductId() {
        XCTAssertEqual(ProManager.paywallProductID, ProManager.baseProductID)
        XCTAssertEqual(ProManager.paywallProductID, "com.iganapolsky.randomtimer.pro")
    }

    func testUiTestProLaunchArgumentOverridesEntitlementToBase() {
        XCTAssertEqual(
            ProManager.entitlementOverride(forLaunchArguments: ["-ui-test-pro", "true"]),
            .base
        )
    }

    func testUiTestEliteLaunchArgumentOverridesEntitlementToElite() {
        XCTAssertEqual(
            ProManager.entitlementOverride(forLaunchArguments: ["-ui-test-elite", "true"]),
            .elite
        )
    }

    func testLaunchArgumentsWithoutUiTestOverrideReturnNil() {
        XCTAssertNil(ProManager.entitlementOverride(forLaunchArguments: ["-ui-test-state", "running"]))
    }

    func testExpiredProUser_maxSecondsAboveFreeLimit_isClamped() {
        let proConfig = RandomTimer.TimerConfig(
            minSeconds: 0,
            maxSeconds: 3600,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false
        )

        let clamped = proConfig.clamped(isPro: false)

        XCTAssertEqual(clamped.maxSeconds, RandomTimer.TimerConfig.maxSecondsFree,
                       "Expired Pro user must have maxSeconds clamped to free limit")
    }

    func testExpiredProUser_proSoundType_isResetToIntense() {
        let proConfig = RandomTimer.TimerConfig(
            minSeconds: 0,
            maxSeconds: 300,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .klaxon,
            volume: 0.5,
            vibrationEnabled: false
        )

        let clamped = proConfig.clamped(isPro: false)

        XCTAssertEqual(clamped.soundType, RandomTimer.SoundType.intense,
                       "Expired Pro user must have Pro soundType reset to .intense")
    }

    func testExpiredProUser_freeSoundType_isRetained() {
        let config = RandomTimer.TimerConfig(
            minSeconds: 0,
            maxSeconds: 300,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .gentle,
            volume: 0.5,
            vibrationEnabled: false
        )

        let clamped = config.clamped(isPro: false)

        XCTAssertEqual(clamped.soundType, .gentle,
                       "Free soundType must be retained after clamping")
    }

    func testActiveProUser_maxSecondsUpTo3600_isRetained() {
        let proConfig = RandomTimer.TimerConfig(
            minSeconds: 0,
            maxSeconds: 3600,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false,
            useExtendedRange: true
        )

        let clamped = proConfig.clamped(isPro: true)

        XCTAssertEqual(clamped.maxSeconds, 3600,
                       "Active Pro user must retain maxSeconds = 3600")
    }

    func testActiveProUser_proSoundType_isRetained() {
        let proConfig = RandomTimer.TimerConfig(
            minSeconds: 0,
            maxSeconds: 300,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .gong,
            volume: 0.5,
            vibrationEnabled: false
        )

        let clamped = proConfig.clamped(isPro: true)

        XCTAssertEqual(clamped.soundType, .gong,
                       "Active Pro user must retain Pro soundType")
    }

    func testFreeUserConfig_withinFreeLimits_isUnchanged() {
        let freeConfig = RandomTimer.TimerConfig(
            minSeconds: 30,
            maxSeconds: 300,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: true,
            soundType: .gentle,
            volume: 0.7,
            vibrationEnabled: false
        )

        let clamped = freeConfig.clamped(isPro: false)

        XCTAssertEqual(clamped.minSeconds, freeConfig.minSeconds)
        XCTAssertEqual(clamped.maxSeconds, freeConfig.maxSeconds)
        XCTAssertEqual(clamped.soundType, freeConfig.soundType)
        XCTAssertEqual(clamped.volume, freeConfig.volume, accuracy: 0.001)
    }

    func testExpiredProUser_allProSoundTypes_areResetToIntense() {
        let proSounds: [RandomTimer.SoundType] = [.klaxon, .whistle, .buzzer, .gong, .airhorn, .drumRoll, .siren, .bell]

        for sound in proSounds {
            let config = RandomTimer.TimerConfig(
                minSeconds: 0,
                maxSeconds: 300,
                alarmDuration: 10,
                soundType: sound,
                volume: 0.5
            )
            let clamped = config.clamped(isPro: false)
            XCTAssertEqual(clamped.soundType, RandomTimer.SoundType.intense,
                           "Pro sound \(sound) must be clamped to .intense for expired Pro user")
        }
    }

    func testExpiredProUser_highSavedRangeCollapsesToFreeCeiling() {
        let proConfig = RandomTimer.TimerConfig(
            minSeconds: 3300,
            maxSeconds: 3600,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false,
            useExtendedRange: true
        )

        let clamped = proConfig.clamped(isPro: false)

        XCTAssertEqual(clamped.minSeconds, RandomTimer.TimerConfig.maxSecondsFree)
        XCTAssertEqual(clamped.maxSeconds, RandomTimer.TimerConfig.maxSecondsFree)
    }
}
