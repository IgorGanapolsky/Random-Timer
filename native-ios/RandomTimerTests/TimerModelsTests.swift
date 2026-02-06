import XCTest
@testable import RandomTimer

final class TimerConfigTests: XCTestCase {

    func testDefaultConfigHasValidRange() {
        let config = TimerConfig.default

        XCTAssertEqual(config.minSeconds, 30)
        XCTAssertEqual(config.maxSeconds, 120)
        XCTAssertEqual(config.volume, 0.5)
        XCTAssertFalse(config.vibrationEnabled)
    }

    func testConfigAcceptsValidRange() {
        let config = TimerConfig(
            minSeconds: 60,
            maxSeconds: 300,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false
        )

        XCTAssertEqual(config.minDuration, 60.0)
        XCTAssertEqual(config.maxDuration, 300.0)
    }

    func testConfigAcceptsSameMinAndMax() {
        let config = TimerConfig(
            minSeconds: 120,
            maxSeconds: 120,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false
        )

        XCTAssertEqual(config.minSeconds, config.maxSeconds)
    }

    func testConfigCanEnableVibration() {
        let config = TimerConfig(
            minSeconds: 30,
            maxSeconds: 120,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: true
        )

        XCTAssertTrue(config.vibrationEnabled)
    }

    func testDefaultAlarmDurationIs10Seconds() {
        let config = TimerConfig.default
        XCTAssertEqual(config.alarmDuration, 10)
    }

    func testConfigDurationConversion() {
        let config = TimerConfig(minSeconds: 90, maxSeconds: 180)
        XCTAssertEqual(config.minDuration, 90.0)
        XCTAssertEqual(config.maxDuration, 180.0)
        XCTAssertEqual(config.alarmDurationInterval, 10.0)
    }
}

final class TimerStateTests: XCTestCase {

    private let defaultConfig = TimerConfig.default

    func testProgressIsZeroAtStart() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 300,
            status: .running
        )

        XCTAssertEqual(state.progress, 0.0, accuracy: 0.001)
    }

    func testProgressIsHalfAtHalfway() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 600,
            remainingDuration: 300,
            status: .running
        )

        XCTAssertEqual(state.progress, 0.5, accuracy: 0.001)
    }

    func testProgressIsOneWhenComplete() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 0,
            status: .complete
        )

        XCTAssertEqual(state.progress, 1.0, accuracy: 0.001)
    }

    func testIsCompleteTrueWhenStatusIsComplete() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 0,
            status: .complete
        )

        XCTAssertTrue(state.isComplete)
    }

    func testIsCompleteTrueWhenStatusIsAlarm() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 0,
            status: .alarm
        )

        XCTAssertTrue(state.isComplete)
    }

    func testIsCompleteFalseWhenStillRunning() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 120,
            status: .running
        )

        XCTAssertFalse(state.isComplete)
    }

    func testProgressHandlesZeroTargetDuration() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 0,
            remainingDuration: 0,
            status: .complete
        )

        XCTAssertEqual(state.progress, 0.0)
    }

    func testTimeRemainingSeconds() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 125.7,
            status: .running
        )

        XCTAssertEqual(state.timeRemainingSeconds, 125)
    }
}

final class TimerStatusTests: XCTestCase {

    func testStatusFromReturnsCompleteAtZero() {
        let status = TimerStatus.from(remainingSeconds: 0, currentStatus: .running)
        XCTAssertEqual(status, .complete)
    }

    func testStatusFromReturnsRunningAboveZero() {
        let status = TimerStatus.from(remainingSeconds: 31, currentStatus: .running)
        XCTAssertEqual(status, .running)
    }

    func testStatusFromPreservesPaused() {
        let status = TimerStatus.from(remainingSeconds: 120, currentStatus: .paused)
        XCTAssertEqual(status, .paused)
    }

    func testStatusFromReturnsCompleteWhenNegative() {
        let status = TimerStatus.from(remainingSeconds: -5, currentStatus: .running)
        XCTAssertEqual(status, .complete)
    }
}

final class TimeIntervalExtensionTests: XCTestCase {

    func testFormattedMMSSMinutesAndSeconds() {
        let interval: TimeInterval = 150 // 2:30
        XCTAssertEqual(interval.formattedMMSS, "02:30")
    }

    func testFormattedMMSSPadsSingleDigits() {
        let interval: TimeInterval = 305 // 5:05
        XCTAssertEqual(interval.formattedMMSS, "05:05")
    }

    func testFormattedMMSSHandlesZero() {
        let interval: TimeInterval = 0
        XCTAssertEqual(interval.formattedMMSS, "00:00")
    }

    func testFormattedMMSSHandlesNegative() {
        let interval: TimeInterval = -5
        XCTAssertEqual(interval.formattedMMSS, "00:00")
    }

    func testFormattedDurationSeconds() {
        let interval: TimeInterval = 45
        XCTAssertEqual(interval.formattedDuration, "45s")
    }

    func testFormattedDurationMinutesOnly() {
        let interval: TimeInterval = 120
        XCTAssertEqual(interval.formattedDuration, "2m")
    }

    func testFormattedDurationMinutesAndSeconds() {
        let interval: TimeInterval = 90
        XCTAssertEqual(interval.formattedDuration, "1m 30s")
    }

    func testMinutesAndSecondsComponents() {
        let interval: TimeInterval = 150
        XCTAssertEqual(interval.minutes, 2)
        XCTAssertEqual(interval.seconds, 30)
    }
}
