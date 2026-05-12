import XCTest
@testable import RandomTimer

final class TimerConfigProClampingTests: XCTestCase {
    @MainActor
    func testPaywallHiddenUnlockHoldDurationIsEightSeconds() {
        XCTAssertEqual(PaywallSheet.hiddenUnlockHoldDuration, 8.0, accuracy: 0.001)
    }

    @MainActor
    func testPaywallCopyFocusesOnTrainingOutcomes() {
        XCTAssertEqual(PaywallSheet.headline, "Unlock Full Fight-Ready Training")
        XCTAssertEqual(
            PaywallSheet.subheadline,
            "Unlock 60-minute random windows, combat voice callouts, round-capped loops, "
                + "and the full sound arsenal built for pressure drills."
        )
        let expectedFooter =
            "Cancel anytime. Subscription auto-renews until cancelled. "
            + "Price shown on Apple's confirmation sheet."
        XCTAssertEqual(PaywallSheet.subscriptionFooter, expectedFooter)
        XCTAssertEqual(
            PaywallSheet.featureRows,
            [
                "60-minute random windows for full-length drills",
                "Combat and MMA voice callouts with live time checks",
                "Round-capped loops for pad work, sparring, and circuits",
                "Full sound arsenal — bells, horns, sirens, and more",
                "Fresh pro audio drops when new packs land",
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
        XCTAssertEqual(PaywallSheet.headlineOutcomesFirst, "Finish Strong With Full Random Pressure")
    }

    func testPaywallFeatureContextExplainsSelectedGateValue() {
        let setupContext = paywallFeatureContext(for: .setupUpgradeCTA)
        XCTAssertEqual(setupContext.eyebrow, "You tapped Unlock Pro")
        XCTAssertEqual(PaywallEntryPoint.setupUpgradeCTA.featureGateName, "setup_upgrade_cta")

        let rangeContext = paywallFeatureContext(for: .rangeGate)
        XCTAssertEqual(rangeContext.eyebrow, "You tapped 60-minute random windows")
        XCTAssertEqual(
            rangeContext.valueCopy,
            "Pro removes the 5-minute cap so long rounds, circuits, and stress drills can run on your timing."
        )

        XCTAssertEqual(paywallFeatureContext(for: .unknown).eyebrow, "Pro Tactical")
    }

    func testPaywallUsesApprovedAppStoreConnectProductId() {
        XCTAssertEqual(ProManager.paywallProductID, ProManager.baseProductID)
        XCTAssertEqual(ProManager.paywallProductID, "com.iganapolsky.randomtimer.pro")
    }

    func testSetupUpgradeDefaultsToLifetimePlan() {
        XCTAssertEqual(
            initialPaywallPlanSelection(entryPoint: .setupUpgradeCTA, defaultToAnnualExperiment: false),
            .lifetime
        )
        XCTAssertEqual(
            initialPaywallPlanSelection(entryPoint: .rangeGate, defaultToAnnualExperiment: false),
            .monthly
        )
        XCTAssertEqual(
            initialPaywallPlanSelection(entryPoint: .setupUpgradeCTA, defaultToAnnualExperiment: true),
            .annual
        )
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

    func testReviewPromptMilestonesAdvancePredictably() {
        XCTAssertNil(reviewPromptMilestone(for: 2))
        XCTAssertEqual(reviewPromptMilestone(for: 3), 3)
        XCTAssertEqual(reviewPromptMilestone(for: 9), 3)
        XCTAssertEqual(reviewPromptMilestone(for: 10), 10)
        XCTAssertEqual(reviewPromptMilestone(for: 24), 10)
        XCTAssertEqual(reviewPromptMilestone(for: 25), 25)
        XCTAssertEqual(reviewPromptMilestone(for: 74), 50)
    }

    func testReviewPromptRequiresNewMilestone() {
        XCTAssertFalse(
            isEligibleForReviewPrompt(
                completionCount: 4,
                lastPromptMilestone: 3,
                lastReviewTimestamp: 0,
                now: 86_400,
                minDaysBetweenRequests: 30
            )
        )
    }

    func testReviewPromptRespectsCooldownAtNewMilestone() {
        let now: TimeInterval = 40 * 86_400
        XCTAssertFalse(
            isEligibleForReviewPrompt(
                completionCount: 10,
                lastPromptMilestone: 3,
                lastReviewTimestamp: now - (10 * 86_400),
                now: now,
                minDaysBetweenRequests: 30
            )
        )
    }

    func testReviewPromptAllowsEarnedRepeatAfterCooldown() {
        let now: TimeInterval = 40 * 86_400
        XCTAssertTrue(
            isEligibleForReviewPrompt(
                completionCount: 10,
                lastPromptMilestone: 3,
                lastReviewTimestamp: now - (31 * 86_400),
                now: now,
                minDaysBetweenRequests: 30
            )
        )
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
