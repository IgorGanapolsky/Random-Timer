import XCTest
import Foundation
@testable import RandomTimer

final class TimerConfigTests: XCTestCase {

    func testDefaultConfigHasValidRange() {
        let config = RandomTimer.TimerConfig.default

        XCTAssertEqual(config.minSeconds, 5)
        XCTAssertEqual(config.maxSeconds, 30)
        XCTAssertEqual(config.alarmDuration, 10)
        XCTAssertFalse(config.voiceEnabled)
    }

    func testLegacyActivationPresetMigrates30To120FreeRange() {
        let legacy = TimerConfig(minSeconds: 30, maxSeconds: 120)
        let next = legacy.applyingLegacyActivationRangePresetIfEligible()
        XCTAssertNotNil(next)
        XCTAssertEqual(next?.minSeconds, 5)
        XCTAssertEqual(next?.maxSeconds, 30)
        XCTAssertEqual(next?.soundType, legacy.soundType)
    }

    func testLegacyActivationPresetSkippedWhenAlreadyOnNewDefault() {
        let next = TimerConfig.default
            .applyingLegacyActivationRangePresetIfEligible()
        XCTAssertNil(next)
    }

    func testLegacyActivationPresetStillMigratesLegacy30To120Shape() {
        let legacy = TimerConfig(minSeconds: 30, maxSeconds: 120)
        let next = legacy.applyingLegacyActivationRangePresetIfEligible()
        XCTAssertNotNil(next)
    }

    func testLegacyActivationPresetSkippedWhenRangeCustomized() {
        let custom = TimerConfig(minSeconds: 45, maxSeconds: 120)
        let next = custom.applyingLegacyActivationRangePresetIfEligible()
        XCTAssertNil(next)
    }

    func testLegacyActivationPresetSkippedWhenExtendedRange() {
        let ext = TimerConfig(minSeconds: 30, maxSeconds: 120, useExtendedRange: true)
        let next = ext.applyingLegacyActivationRangePresetIfEligible()
        XCTAssertNil(next)
    }

    func testConfigCanEnableVibration() {
        let config = RandomTimer.TimerConfig(
            minSeconds: 30,
            maxSeconds: 60,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: true,
            useExtendedRange: false,
            voiceEnabled: true,
            repeatRounds: 0
        )

        XCTAssertTrue(config.vibrationEnabled)
    }

    func testConfigDecodingFromLooseJSON() throws {
        // Test that our custom decoder handles various formats (strings, numbers, etc)
        let payload = Data("""
        {
          "min_seconds": "0",
          "max_seconds": 3600,
          "alarm_duration": "1",
          "hidden_mode": "true",
          "repeat_enabled": "1",
          "sound_type": "DRUM_ROLL",
          "soundVolume": "1.5",
          "vibration": "yes",
          "useExtendedRange": true,
          "voiceEnabled": false,
          "repeatRounds": 5
        }
        """.utf8)

        let decoded = try JSONDecoder().decode(RandomTimer.TimerConfig.self, from: payload)

        XCTAssertEqual(decoded.minSeconds, 5)
        XCTAssertEqual(decoded.maxSeconds, RandomTimer.TimerConfig.maxSecondsPro)
        XCTAssertEqual(decoded.alarmDuration, 1)
        XCTAssertTrue(decoded.hiddenMode)
        XCTAssertTrue(decoded.repeatEnabled)
        XCTAssertEqual(decoded.soundType, .drumRoll)
        XCTAssertEqual(decoded.volume, 1.0, accuracy: 0.0001)
        XCTAssertTrue(decoded.vibrationEnabled)
        XCTAssertFalse(decoded.voiceEnabled)
        XCTAssertEqual(decoded.repeatRounds, 5)
    }

    func testConfigEncodingRoundTripsVoiceCalloutsFlag() throws {
        let config = TimerConfig(
            minSeconds: 15,
            maxSeconds: 45,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: true,
            soundType: .gentle,
            volume: 0.7,
            vibrationEnabled: true,
            useExtendedRange: false,
            voiceEnabled: true,
            repeatRounds: 0
        )

        let encoded = try JSONEncoder().encode(config)
        let decoded = try JSONDecoder().decode(TimerConfig.self, from: encoded)

        XCTAssertEqual(decoded, config)
    }

    func testConfigDecodingFallsBackToDefaultsWhenFieldsMissing() throws {
        let payload = Data("{}".utf8)
        let decoded = try JSONDecoder().decode(RandomTimer.TimerConfig.self, from: payload)

        let expected = RandomTimer.TimerConfig(
            minSeconds: 5,
            maxSeconds: 30,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false,
            useExtendedRange: false,
            voiceEnabled: false,
            repeatRounds: 0
        )
        XCTAssertEqual(decoded, expected)
    }

    func testConfigInitSanitizesInvalidInputs() {
        let config = RandomTimer.TimerConfig(
            minSeconds: -20,
            maxSeconds: 5000,
            alarmDuration: 0,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 1.5,
            vibrationEnabled: false,
            useExtendedRange: false,
            voiceEnabled: true,
            repeatRounds: -4
        )

        XCTAssertEqual(config.minSeconds, 5)
        XCTAssertEqual(config.maxSeconds, RandomTimer.TimerConfig.maxSecondsPro)
        XCTAssertEqual(config.alarmDuration, 1)
        XCTAssertEqual(config.volume, 1.0, accuracy: 0.0001)
        XCTAssertEqual(config.repeatRounds, 0)
    }

    func testConfigInitPullsMinDownWhenRangeIsInverted() {
        let config = RandomTimer.TimerConfig(
            minSeconds: 240,
            maxSeconds: 90,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false,
            useExtendedRange: false,
            voiceEnabled: true,
            repeatRounds: 0
        )

        XCTAssertEqual(config.minSeconds, 90)
        XCTAssertEqual(config.maxSeconds, 90)
    }

    func testConfigDecodingSanitizesInvertedLegacyRange() throws {
        let payload = Data("""
        {
          "min_seconds": 600,
          "max_seconds": 45,
          "alarm_duration": 10,
          "sound_type": "intense",
          "soundVolume": 0.5
        }
        """.utf8)

        let decoded = try JSONDecoder().decode(RandomTimer.TimerConfig.self, from: payload)

        XCTAssertEqual(decoded.minSeconds, 45)
        XCTAssertEqual(decoded.maxSeconds, 45)
    }

    func testAdjustForMinChangeSafelyClampsWhenRangeLimitDrops() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 3300,
            currentMaxSeconds: 3600,
            newMinSeconds: 3300,
            maxSecondsLimit: TimerConfig.maxSecondsFree
        )

        XCTAssertEqual(adjusted.min, 295)
        XCTAssertEqual(adjusted.max, TimerConfig.maxSecondsFree)
        XCTAssertGreaterThanOrEqual(
            adjusted.max - adjusted.min,
            TimeRangeAdjuster.defaultMinGapSeconds
        )
    }

    func testAdjustForMaxChangeSafelyClampsWhenRangeLimitDrops() {
        let adjusted = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: 3300,
            currentMaxSeconds: 3600,
            newMaxSeconds: 3600,
            maxSecondsLimit: TimerConfig.maxSecondsFree
        )

        XCTAssertEqual(adjusted.min, 295)
        XCTAssertEqual(adjusted.max, TimerConfig.maxSecondsFree)
        XCTAssertGreaterThanOrEqual(
            adjusted.max - adjusted.min,
            TimeRangeAdjuster.defaultMinGapSeconds
        )
    }

    func testToggleExtendedRangeRestoresLastFreeRange() {
        let current = TimerConfig(
            minSeconds: 900,
            maxSeconds: 1800,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false,
            useExtendedRange: true,
            voiceEnabled: true,
            repeatRounds: 0
        )
        let profiles = RangeToggleProfiles(
            freeMinSeconds: 5,
            freeMaxSeconds: 30,
            extendedMinSeconds: 900,
            extendedMaxSeconds: 1800
        )

        let result = toggleExtendedRange(current: current, profiles: profiles)

        XCTAssertFalse(result.config.useExtendedRange)
        XCTAssertEqual(result.config.minSeconds, 5)
        XCTAssertEqual(result.config.maxSeconds, 30)
        XCTAssertEqual(result.profiles.extendedMinSeconds, 900)
        XCTAssertEqual(result.profiles.extendedMaxSeconds, 1800)
    }

    func testToggleExtendedRangeRestoresLastExtendedRange() {
        let current = TimerConfig(
            minSeconds: 45,
            maxSeconds: 180,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false,
            useExtendedRange: false,
            voiceEnabled: true,
            repeatRounds: 0
        )
        let profiles = RangeToggleProfiles(
            freeMinSeconds: 45,
            freeMaxSeconds: 180,
            extendedMinSeconds: 1200,
            extendedMaxSeconds: 2400
        )

        let result = toggleExtendedRange(current: current, profiles: profiles)

        XCTAssertTrue(result.config.useExtendedRange)
        XCTAssertEqual(result.config.minSeconds, 1200)
        XCTAssertEqual(result.config.maxSeconds, 2400)
        XCTAssertEqual(result.profiles.freeMinSeconds, 45)
        XCTAssertEqual(result.profiles.freeMaxSeconds, 180)
    }
}

final class TimerStateTests: XCTestCase {

    private let defaultConfig = RandomTimer.TimerConfig.default

    func testProgressIsZeroAtStart() {
        let state = RandomTimer.TimerState(
            config: defaultConfig,
            targetDuration: 300,
            startedAt: Date(),
            remainingDuration: 300,
            status: .running,
            roundCount: 1
        )

        XCTAssertEqual(state.progress, 0.0, accuracy: 0.001)
    }

    func testProgressIsHalfAtHalfway() {
        let state = RandomTimer.TimerState(
            config: defaultConfig,
            targetDuration: 600,
            startedAt: Date(),
            remainingDuration: 300,
            status: .running,
            roundCount: 1
        )

        XCTAssertEqual(state.progress, 0.5, accuracy: 0.001)
    }

    func testProgressIsOneWhenComplete() {
        let state = RandomTimer.TimerState(
            config: defaultConfig,
            targetDuration: 300,
            startedAt: Date(),
            remainingDuration: 0,
            status: .complete,
            roundCount: 1
        )

        XCTAssertEqual(state.progress, 1.0, accuracy: 0.001)
    }

    func testIsCompleteTrueWhenStatusIsComplete() {
        let state = RandomTimer.TimerState(
            config: defaultConfig,
            targetDuration: 300,
            startedAt: Date(),
            remainingDuration: 0,
            status: .complete,
            roundCount: 1
        )

        XCTAssertTrue(state.isComplete)
    }
}

final class CompetitionWarmupRemovalGuardTests: XCTestCase {
    private let forbiddenFragments = [
        "Competition Warmup",
        "Competition Prep",
        "STANDARD OPS",
        "TrainingPreset",
        "competition_warmup",
        "onTrainingPresetApplied",
        "showCompetitionPrep",
    ]

    private let guardedRelativePaths = [
        "RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift",
        "SharedModels/TimerModels.swift",
        "RandomTimer/Sources/Services/TimerManager.swift",
    ]

    func testTimerSetupSourcesContainNoCompetitionWarmupUi() throws {
        let repoRoot = try XCTUnwrap(locateRepoRoot())
        for relativePath in guardedRelativePaths {
            let fileURL = repoRoot.appendingPathComponent("native-ios").appendingPathComponent(relativePath)
            let source = try String(contentsOf: fileURL, encoding: .utf8)
            for fragment in forbiddenFragments {
                XCTAssertFalse(
                    source.range(of: fragment, options: .caseInsensitive) != nil,
                    "\(relativePath) must not contain '\(fragment)'"
                )
            }
        }
    }

    private func locateRepoRoot() -> URL? {
        var current = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        while current.path != "/" {
            if FileManager.default.fileExists(atPath: current.appendingPathComponent("native-ios").path) {
                return current
            }
            current.deleteLastPathComponent()
        }
        return nil
    }
}
