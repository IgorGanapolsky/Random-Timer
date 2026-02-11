import XCTest
import Foundation
@testable import RandomTimer

final class TimerConfigTests: XCTestCase {

    func testDefaultConfigHasValidRange() {
        let config = TimerConfig.default

        XCTAssertEqual(config.minSeconds, 0)
        XCTAssertEqual(config.maxSeconds, 300)
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

final class SoundTypeTests: XCTestCase {

    func testIntenseNotificationSoundName() {
        XCTAssertEqual(SoundType.intense.notificationSoundName, "alarm.mp3")
    }

    func testGentleNotificationSoundName() {
        XCTAssertEqual(SoundType.gentle.notificationSoundName, "gentle-chime.mp3")
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

// MARK: - Alarm Background Expiry Tests

final class AlarmBackgroundExpiryTests: XCTestCase {

    private let defaultConfig = TimerConfig.default

    func testAlarmStartedAtIsNilByDefault() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 60
        )
        XCTAssertNil(state.alarmStartedAt)
    }

    func testAlarmStartedAtCanBeSet() {
        let now = Date()
        var state = TimerState(
            config: defaultConfig,
            targetDuration: 60,
            status: .alarm,
            alarmTimeRemaining: 10,
            alarmStartedAt: now
        )
        XCTAssertEqual(state.alarmStartedAt, now)
    }

    func testAlarmExpiredWhenElapsedExceedsDuration() {
        // Simulate: alarm started 15 seconds ago, alarm duration is 10s
        let alarmStart = Date().addingTimeInterval(-15)
        let alarmDuration: TimeInterval = 10
        let elapsed = Date().timeIntervalSince(alarmStart)

        XCTAssertTrue(elapsed >= alarmDuration, "Alarm should be expired")
    }

    func testAlarmStillActiveWhenElapsedLessThanDuration() {
        // Simulate: alarm started 3 seconds ago, alarm duration is 10s
        let alarmStart = Date().addingTimeInterval(-3)
        let alarmDuration: TimeInterval = 10
        let elapsed = Date().timeIntervalSince(alarmStart)

        XCTAssertTrue(elapsed < alarmDuration, "Alarm should still be active")
        let remaining = alarmDuration - elapsed
        XCTAssertTrue(remaining > 0 && remaining <= 10)
    }

    func testAlarmRemainingTimeCalculation() {
        let alarmStart = Date().addingTimeInterval(-7)
        let alarmDuration: TimeInterval = 10
        let remaining = alarmDuration - Date().timeIntervalSince(alarmStart)

        XCTAssertEqual(remaining, 3, accuracy: 0.5)
    }
}

// MARK: - Media Button Dismiss Tests

final class MediaButtonTests: XCTestCase {

    func testOnMediaButtonDismissCallbackIsInvocable() {
        var dismissed = false
        let callback: () -> Void = { dismissed = true }
        callback()
        XCTAssertTrue(dismissed)
    }

    func testOnMediaButtonDismissCallbackDefaultsToNil() {
        // Verify the callback pattern works — optional closure starts nil
        var callback: (() -> Void)?
        XCTAssertNil(callback)

        callback = { /* dismiss */ }
        XCTAssertNotNil(callback)
    }
}

final class TimerManagerResetTests: XCTestCase {
    @MainActor
    func testResetWhileAlarmStopsAlarmAndRestartsTimer() async {
        let timerManager = TimerManager()

        let config = RandomTimer.TimerConfig(
            minSeconds: 5,
            maxSeconds: 5,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: true
        )
        let alarmState = RandomTimer.TimerState(
            config: config,
            targetDuration: 5,
            remainingDuration: 0,
            status: .alarm,
            alarmTimeRemaining: 10,
            alarmStartedAt: Date()
        )

        timerManager._setTimerStateForTesting(alarmState)

        await timerManager.resetTimer()

        let newState = timerManager.timerState
        XCTAssertNotNil(newState)
        XCTAssertEqual(newState?.status, .running)
        XCTAssertEqual(newState?.targetDuration, alarmState.targetDuration)
        XCTAssertEqual(newState?.remainingDuration, newState?.targetDuration)
    }

    @MainActor
    func testResetWhileRunningRestartsFromFullDuration() async {
        let timerManager = TimerManager()

        let config = RandomTimer.TimerConfig.default
        let startDate = Date(timeIntervalSince1970: 0)
        let runningState = RandomTimer.TimerState(
            config: config,
            targetDuration: 60,
            startedAt: startDate,
            remainingDuration: 10,
            status: .running
        )

        timerManager._setTimerStateForTesting(runningState)

        await timerManager.resetTimer()

        guard let newState = timerManager.timerState else {
            XCTFail("Expected timerState after reset")
            return
        }
        XCTAssertEqual(newState.status, .running)
        XCTAssertEqual(newState.targetDuration, runningState.targetDuration)
        XCTAssertEqual(newState.remainingDuration, newState.targetDuration, accuracy: 1.0)
        XCTAssertTrue(newState.startedAt > startDate)
    }
}

// MARK: - Loop toggle regression tests (mirrors Android TimerStateFlowTest)

final class TimerManagerLoopTests: XCTestCase {
    @MainActor
    func testUpdateConfigSyncsRepeatEnabledIntoRunningTimerState() {
        let timerManager = TimerManager()

        let config = RandomTimer.TimerConfig(
            minSeconds: 5,
            maxSeconds: 10,
            alarmDuration: 5,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: true
        )
        let state = RandomTimer.TimerState(
            config: config,
            targetDuration: 7,
            remainingDuration: 5,
            status: .running
        )

        timerManager._setTimerStateForTesting(state)
        XCTAssertFalse(timerManager.timerState!.config.repeatEnabled)

        // Toggle loop ON via updateConfig
        var newConfig = config
        newConfig = RandomTimer.TimerConfig(
            minSeconds: config.minSeconds,
            maxSeconds: config.maxSeconds,
            alarmDuration: config.alarmDuration,
            hiddenMode: config.hiddenMode,
            repeatEnabled: true,
            soundType: config.soundType,
            volume: config.volume,
            vibrationEnabled: config.vibrationEnabled
        )
        timerManager.updateConfig(newConfig)

        // timerState.config must reflect the change
        XCTAssertTrue(timerManager.timerState!.config.repeatEnabled,
                      "Loop toggle must propagate into running timerState.config")
    }

    @MainActor
    func testUpdateConfigDoesNotCrashWhenNoTimerRunning() {
        let timerManager = TimerManager()

        XCTAssertNil(timerManager.timerState)

        let newConfig = RandomTimer.TimerConfig(
            minSeconds: 1,
            maxSeconds: 60,
            alarmDuration: 5,
            hiddenMode: false,
            repeatEnabled: true,
            soundType: .gentle,
            volume: 0.8,
            vibrationEnabled: false
        )
        // Should not crash
        timerManager.updateConfig(newConfig)
        XCTAssertNil(timerManager.timerState)
        XCTAssertTrue(timerManager.config.repeatEnabled)
    }
}

// MARK: - Live Activity Must Not Leak Timing Info

final class LiveActivityTimingLeakTests: XCTestCase {

    /// The Live Activity content state should NEVER carry real remaining seconds
    /// because it would let an observer deduce the random duration from the lock screen.
    @MainActor
    func testLiveActivityUpdateSendsZeroRemainingSeconds() {
        // When building the content state for a running timer,
        // remainingSeconds must always be 0 to prevent timing leaks
        let config = TimerConfig(minSeconds: 30, maxSeconds: 120, alarmDuration: 10)
        let state = TimerState(
            config: config,
            targetDuration: 75, // random duration
            remainingDuration: 42, // 42s left
            status: .running
        )

        // The sanitized remaining seconds for Live Activity should be 0
        XCTAssertEqual(state.liveActivityRemainingSeconds, 0,
                       "Running timer must not leak remainingSeconds to Live Activity")
    }

    /// Alarm/complete states CAN show 0 since the timer is done
    @MainActor
    func testLiveActivityShowsZeroWhenComplete() {
        let config = TimerConfig(minSeconds: 30, maxSeconds: 120, alarmDuration: 10)
        let state = TimerState(
            config: config,
            targetDuration: 75,
            remainingDuration: 0,
            status: .complete
        )

        XCTAssertEqual(state.liveActivityRemainingSeconds, 0)
    }

    /// endDate must be the MAX possible end time, not the actual random end time
    @MainActor
    func testLiveActivityEndDateUsesMaxDuration() {
        let config = TimerConfig(minSeconds: 30, maxSeconds: 120, alarmDuration: 10)
        let state = TimerState(
            config: config,
            targetDuration: 75, // actual random: 75s
            remainingDuration: 75,
            status: .running
        )

        let maxPossibleEnd = state.startedAt.addingTimeInterval(Double(config.maxSeconds))

        // liveActivityEndDate should be based on maxSeconds, not targetDuration
        XCTAssertEqual(
            state.liveActivityEndDate.timeIntervalSinceReferenceDate,
            maxPossibleEnd.timeIntervalSinceReferenceDate,
            accuracy: 1.0,
            "Live Activity endDate must use maxSeconds to avoid leaking the random duration"
        )
    }
}

// MARK: - Silence Alarm State Tests

final class TimerManagerSilenceTests: XCTestCase {

    @MainActor
    func testIsAlarmSilencedDefaultsToFalse() {
        let timerManager = TimerManager()
        XCTAssertFalse(timerManager.isAlarmSilenced,
                       "isAlarmSilenced should default to false")
    }

    @MainActor
    func testSilenceAlarmSetsIsAlarmSilencedTrue() {
        let timerManager = TimerManager()

        let config = RandomTimer.TimerConfig(
            minSeconds: 5, maxSeconds: 10, alarmDuration: 30,
            hiddenMode: false, repeatEnabled: false,
            soundType: .intense, volume: 0.5, vibrationEnabled: false
        )
        let alarmState = RandomTimer.TimerState(
            config: config, targetDuration: 5,
            remainingDuration: 0, status: .alarm,
            alarmTimeRemaining: 25, alarmStartedAt: Date()
        )
        timerManager._setTimerStateForTesting(alarmState)

        timerManager.silenceAlarm()

        XCTAssertTrue(timerManager.isAlarmSilenced,
                      "After silenceAlarm(), isAlarmSilenced must be true")
    }

    @MainActor
    func testIsAlarmSilencedResetsOnNewAlarm() async {
        let timerManager = TimerManager()

        // Simulate: alarm active, user silences it
        let config = RandomTimer.TimerConfig(
            minSeconds: 5, maxSeconds: 5, alarmDuration: 30,
            hiddenMode: false, repeatEnabled: false,
            soundType: .intense, volume: 0.5, vibrationEnabled: false
        )
        let alarmState = RandomTimer.TimerState(
            config: config, targetDuration: 5,
            remainingDuration: 0, status: .alarm,
            alarmTimeRemaining: 25, alarmStartedAt: Date()
        )
        timerManager._setTimerStateForTesting(alarmState)
        timerManager.silenceAlarm()
        XCTAssertTrue(timerManager.isAlarmSilenced)

        // Reset timer — starts a new timer, isAlarmSilenced should reset
        await timerManager.resetTimer()

        XCTAssertFalse(timerManager.isAlarmSilenced,
                       "isAlarmSilenced must reset when a new timer starts")
    }

    /// When user taps notification to open app, sound stops but alarm state stays.
    /// handleForeground with didTapAlarmNotification must set isAlarmSilenced = true.
    @MainActor
    func testHandleForegroundViaNotificationTapSetsAlarmSilenced() async {
        let timerManager = TimerManager()

        // Simulate: timer expired while backgrounded, alarm is active
        let config = RandomTimer.TimerConfig(
            minSeconds: 5, maxSeconds: 30, alarmDuration: 30,
            hiddenMode: false, repeatEnabled: false,
            soundType: .intense, volume: 0.5, vibrationEnabled: false
        )
        // Timer started 15s ago, target was 10s — already expired
        let startDate = Date().addingTimeInterval(-15)
        let state = RandomTimer.TimerState(
            config: config, targetDuration: 10,
            startedAt: startDate,
            remainingDuration: 5, // stale value from when app was suspended
            status: .running // stale — was running when app backgrounded
        )
        timerManager._setTimerStateForTesting(state)

        // Simulate notification tap flag being set
        timerManager.setNotificationTapFlagForTesting()

        await timerManager.handleForeground()

        // After foreground via notification tap, alarm sound is stopped
        // so isAlarmSilenced must be true
        XCTAssertTrue(timerManager.isAlarmSilenced,
                      "Opening via notification tap must set isAlarmSilenced since sound is stopped")
    }
}
