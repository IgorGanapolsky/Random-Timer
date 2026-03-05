import XCTest
import Foundation
@testable import RandomTimer

final class SilenceAndStopAlarmTests: XCTestCase {

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
}
