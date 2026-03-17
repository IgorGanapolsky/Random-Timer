import XCTest
@testable import RandomTimer

final class TimerConfigProClampingTests: XCTestCase {

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
            vibrationEnabled: false
        )

        let clamped = proConfig.clamped(isPro: true)

        XCTAssertEqual(clamped.maxSeconds, 3600,
                       "Active Pro user must retain maxSeconds = 3600")
        XCTAssertTrue(clamped.useExtendedRange,
                      "Active Pro user should normalize legacy extended-range configs")
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
}
