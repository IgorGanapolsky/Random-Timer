import XCTest
import Foundation
@testable import RandomTimer

final class SilenceAndStopAlarmTests: XCTestCase {

    override func setUp() {
        super.setUp()
        UserDefaults.standard.removeObject(forKey: "active_timer_state")
        UserDefaults.standard.removeObject(forKey: "timer_config")
    }

    @MainActor
    private func makeConfig() -> TimerConfig {
        TimerConfig(
            minSeconds: 5,
            maxSeconds: 300,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false
        )
    }

    @MainActor
    private func makeState(
        config: TimerConfig? = nil,
        status: TimerStatus = .running
    ) -> TimerState {
        return TimerState(
            config: config ?? makeConfig(),
            targetDuration: 10,
            startedAt: Date(),
            remainingDuration: 10,
            status: status
        )
    }

    @MainActor
    func testSilenceAlarmStopsAudioButKeepsState() async {
        let manager = TimerManager()
        let config = makeConfig()
        let state = TimerState(
            config: config,
            targetDuration: 5,
            remainingDuration: 0,
            status: .alarm,
            alarmTimeRemaining: 10,
            alarmStartedAt: Date()
        )
        manager._setTimerStateForTesting(state)

        manager.silenceAlarm()

        XCTAssertTrue(manager.isAlarmSilenced)
        XCTAssertEqual(manager.timerState?.status, .alarm)
    }

    @MainActor
    func testDismissAlarmStopsAudioAndClearsState() async {
        let manager = TimerManager()
        let state = makeState(status: .alarm)
        manager._setTimerStateForTesting(state)

        await manager.dismissAlarm()

        XCTAssertNil(manager.timerState)
        XCTAssertFalse(manager.isAlarmSilenced)
    }

    @MainActor
    func testDoesNotClearTimerState() {
        let manager = TimerManager()
        let state = makeState(status: .running)
        manager._setTimerStateForTesting(state)

        manager.silenceAlarm()

        XCTAssertNotNil(manager.timerState)
        XCTAssertFalse(manager.isAlarmSilenced)
    }

    @MainActor
    func testDoesNothingWhenRunning() {
        let manager = TimerManager()
        let state = makeState(status: .running)
        manager._setTimerStateForTesting(state)

        manager.silenceAlarm()

        XCTAssertEqual(manager.timerState?.status, .running)
        XCTAssertFalse(manager.isAlarmSilenced)
    }

    @MainActor
    func testDoesNothingWhenComplete() {
        let manager = TimerManager()
        let state = makeState(status: .complete)
        manager._setTimerStateForTesting(state)

        manager.silenceAlarm()

        XCTAssertEqual(manager.timerState?.status, .complete)
        XCTAssertFalse(manager.isAlarmSilenced)
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
        let state = TimerState(
            config: makeConfig(),
            targetDuration: 5,
            remainingDuration: 0,
            status: .alarm,
            alarmTimeRemaining: 5,
            alarmStartedAt: Date()
        )
        manager._setTimerStateForTesting(state)

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
        let state = makeState(status: .running)
        manager._setTimerStateForTesting(state)

        manager.handleBackground()

        // Should not set silenced flag when not in alarm state
        XCTAssertFalse(manager.isAlarmSilenced)
        XCTAssertEqual(manager.timerState?.status, .running)
    }

    @MainActor
    func testPreservesLoopConfig() {
        let manager = TimerManager()
        let config = TimerConfig(repeatEnabled: true)
        let state = TimerState(
            config: config,
            targetDuration: 5,
            remainingDuration: 0,
            status: .alarm,
            alarmTimeRemaining: 5,
            alarmStartedAt: Date()
        )
        manager._setTimerStateForTesting(state)

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

    func testNotificationDismissActionSetsTapFlagAndInvokesStopCallback() {
        let service = NotificationService()
        var didStop = false

        service.onNotificationStop = { didStop = true }

        service.handleNotificationDismissAction()

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
