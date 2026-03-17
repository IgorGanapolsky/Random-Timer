import XCTest
import Foundation
@testable import RandomTimer

final class TimerConfigTests: XCTestCase {

    func testDefaultConfigHasValidRange() {
        let config = RandomTimer.TimerConfig.default

        XCTAssertEqual(config.minSeconds, 0)
        XCTAssertEqual(config.maxSeconds, 300)
        XCTAssertEqual(config.alarmDuration, 10)
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
        let payload = """
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
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(RandomTimer.TimerConfig.self, from: payload)

        XCTAssertEqual(decoded.minSeconds, 0)
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
        let payload = "{}".data(using: .utf8)!
        let decoded = try JSONDecoder().decode(RandomTimer.TimerConfig.self, from: payload)
        
        let expected = RandomTimer.TimerConfig(
            minSeconds: 0,
            maxSeconds: 300,
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
        XCTAssertEqual(decoded, expected)
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
