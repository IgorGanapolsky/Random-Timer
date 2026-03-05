import XCTest
@testable import RandomTimer

/// Tests for circle tap during alarm — now calls silenceAlarm() which
/// silences sound/vibration but keeps alarm countdown alive for loop support.
final class SilenceAndStopAlarmTests: XCTestCase {

    private func makeConfig() -> TimerConfig {
        TimerConfig(
            minSeconds: 30,
            maxSeconds: 300,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false
        )
    }

    private func makeAlarmState(
        config: TimerConfig? = nil,
        alarmTimeRemaining: TimeInterval = 8
    ) -> TimerState {
        let cfg = config ?? makeConfig()
        return TimerState(
            config: cfg,
            targetDuration: 300,
            remainingDuration: 0,
            status: .alarm,
            alarmTimeRemaining: alarmTimeRemaining,
            alarmStartedAt: Date()
        )
    }

    @MainActor
    func testKeepsAlarmStatusAfterSilence() {
        let manager = TimerManager()
        manager._setTimerStateForTesting(makeAlarmState())

        manager.silenceAlarm()

        // Status stays .alarm — countdown keeps ticking for loop support
        XCTAssertEqual(manager.timerState?.status, .alarm)
        // alarmTimeRemaining is NOT zeroed
        XCTAssertEqual(manager.timerState?.alarmTimeRemaining, 8)
    }

    @MainActor
    func testSetsIsAlarmSilencedFlag() {
        let manager = TimerManager()
        manager._setTimerStateForTesting(makeAlarmState(alarmTimeRemaining: 5))

        manager.silenceAlarm()

        XCTAssertTrue(manager.isAlarmSilenced)
    }

    @MainActor
    func testDoesNotClearTimerState() {
        let manager = TimerManager()
        manager._setTimerStateForTesting(makeAlarmState(alarmTimeRemaining: 5))

        manager.silenceAlarm()

        // timerState must NOT be nil — user stays on timer screen
        XCTAssertNotNil(manager.timerState)
        XCTAssertEqual(manager.timerState?.targetDuration, 300)
    }

    @MainActor
    func testDoesNothingWhenRunning() {
        let manager = TimerManager()
        let state = TimerState(
            config: makeConfig(),
            targetDuration: 300,
            remainingDuration: 30,
            status: .running
        )
        manager._setTimerStateForTesting(state)

        manager.silenceAlarm()

        XCTAssertEqual(manager.timerState?.status, .running)
    }

    @MainActor
    func testDoesNothingWhenComplete() {
        let manager = TimerManager()
        let state = TimerState(
            config: makeConfig(),
            targetDuration: 300,
            remainingDuration: 0,
            status: .complete
        )
        manager._setTimerStateForTesting(state)

        manager.silenceAlarm()

        XCTAssertEqual(manager.timerState?.status, .complete)
    }

    @MainActor
    func testDoesNothingWhenStateIsNil() {
        let manager = TimerManager()

        manager.silenceAlarm()

        XCTAssertNil(manager.timerState)
    }

    @MainActor
    func testHandleBackgroundSilencesAlarmViaPowerButton() {
        let manager = TimerManager()
        manager._setTimerStateForTesting(makeAlarmState(alarmTimeRemaining: 5))

        // Simulate power button press (app goes to background while alarm is playing)
        manager.handleBackground()

        // Alarm should be silenced so it does NOT restart when returning to foreground
        XCTAssertTrue(manager.isAlarmSilenced, "Power button (background) should silence the alarm")
        // Status stays .alarm — countdown keeps ticking for loop support
        XCTAssertEqual(manager.timerState?.status, .alarm)
    }

    @MainActor
    func testHandleBackgroundDoesNothingWhenNotAlarming() {
        let manager = TimerManager()
        let state = TimerState(
            config: makeConfig(),
            targetDuration: 300,
            remainingDuration: 30,
            status: .running
        )
        manager._setTimerStateForTesting(state)

        manager.handleBackground()

        // Should not set silenced flag when not in alarm state
        XCTAssertFalse(manager.isAlarmSilenced)
        XCTAssertEqual(manager.timerState?.status, .running)
    }

    @MainActor
    func testPreservesLoopConfig() {
        let manager = TimerManager()
        let config = TimerConfig(
            minSeconds: 30,
            maxSeconds: 300,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: true,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false
        )
        manager._setTimerStateForTesting(makeAlarmState(config: config, alarmTimeRemaining: 5))

        manager.silenceAlarm()

        XCTAssertTrue(manager.timerState?.config.repeatEnabled ?? false)
    }
}

@MainActor
final class NotificationServiceMediaButtonBehaviorTests: XCTestCase {

    func testMediaButtonSilenceActionInvokesSilenceCallbackOnly() {
        let service = NotificationService()
        var didSilence = false
        var didStop = false

        service.onMediaButtonSilence = { didSilence = true }
        service.onNotificationStop = { didStop = true }

        service.handleMediaButtonSilenceAction()

        XCTAssertTrue(didSilence)
        XCTAssertFalse(didStop)
    }

    func testNotificationStopActionSetsTapFlagAndInvokesStopCallback() {
        let service = NotificationService()
        var didStop = false

        service.onNotificationStop = { didStop = true }

        service.handleNotificationStopAction()

        XCTAssertTrue(service.didTapAlarmNotification)
        XCTAssertTrue(didStop)
    }

    func testNotificationSilenceActionInvokesSilenceCallback() {
        let service = NotificationService()
        var didSilence = false

        service.onNotificationSilence = { didSilence = true }

        service.handleNotificationSilenceAction()

        XCTAssertTrue(didSilence)
    }
}
