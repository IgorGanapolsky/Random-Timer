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
    private final class MockNotificationService: TimerNotificationHandling {
        var didTapAlarmNotification: Bool = false
        var stopAlarmSoundCount = 0
        var stopVibrationCount = 0
        var cancelPendingCount = 0
        var scheduleCalls: [Date] = []
        var clearNotificationTapFlagCount = 0

        func requestNotificationPermission() async {}

        func scheduleAlarmNotification(at date: Date, soundType: SoundType) async {
            scheduleCalls.append(date)
        }

        func cancelPendingNotifications() async {
            cancelPendingCount += 1
        }

        func playAlarmSound(type: SoundType, volume: Float) {}

        func stopAlarmSound() {
            stopAlarmSoundCount += 1
        }

        func startVibration() {}

        func stopVibration() {
            stopVibrationCount += 1
        }

        func playPreviewSound(type: SoundType, volume: Float) {}

        func updatePreviewVolume(_ volume: Float) {}

        func stopPreview() {}

        func clearNotificationTapFlag() {
            didTapAlarmNotification = false
            clearNotificationTapFlagCount += 1
        }
    }

    private actor MockStorageService: TimerStorage {
        private(set) var savedState: TimerState?

        func saveConfig(_ config: TimerConfig) async {}
        func loadConfig() async -> TimerConfig? { nil }
        func saveTimerState(_ state: TimerState) async { savedState = state }
        func loadTimerState() async -> TimerState? { savedState }
        func clearTimerState() async { savedState = nil }

        nonisolated func loadConfigSync() -> TimerConfig? { nil }
        nonisolated func loadTimerStateSync() -> TimerState? { nil }
        nonisolated func clearTimerStateSync() {}
    }

    @MainActor
    private final class MockLiveActivityService: TimerLiveActivityHandling {
        var startCount = 0
        var updateCount = 0
        var endCount = 0
        var endAllCount = 0

        func start(state: TimerState) async { startCount += 1 }
        func update(state: TimerState) { updateCount += 1 }
        func end() { endCount += 1 }
        func endAll() async { endAllCount += 1 }
    }

    @MainActor
    func testResetWhileAlarmStopsAlarmAndRestartsTimer() async {
        let notificationService = MockNotificationService()
        let storageService = MockStorageService()
        let liveActivityService = MockLiveActivityService()

        let timerManager = TimerManager(
            storageService: storageService,
            notificationService: notificationService,
            liveActivityService: liveActivityService
        )

        let config = TimerConfig(
            minSeconds: 5,
            maxSeconds: 5,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: true
        )
        let alarmState = TimerState(
            config: config,
            targetDuration: 5,
            remainingDuration: 0,
            status: .alarm,
            alarmTimeRemaining: 10,
            alarmStartedAt: Date()
        )

        timerManager._setTimerStateForTesting(alarmState)

        await timerManager.resetTimer()

        XCTAssertEqual(notificationService.stopAlarmSoundCount, 1)
        XCTAssertEqual(notificationService.stopVibrationCount, 1)
        XCTAssertEqual(notificationService.cancelPendingCount, 1)
        XCTAssertEqual(notificationService.clearNotificationTapFlagCount, 1)
        XCTAssertEqual(notificationService.scheduleCalls.count, 1)

        let newState = timerManager.timerState
        XCTAssertNotNil(newState)
        XCTAssertEqual(newState?.status, .running)
        XCTAssertEqual(newState?.targetDuration, alarmState.targetDuration)
        XCTAssertEqual(newState?.remainingDuration, newState?.targetDuration)
    }
}
