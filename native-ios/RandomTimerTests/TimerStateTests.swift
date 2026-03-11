import XCTest
import Foundation
@testable import RandomTimer

final class TimerStateTests: XCTestCase {

    func testProgressIsZeroAtStart() {
        let state = TimerState(config: .default, targetDuration: 100, remainingDuration: 100)
        XCTAssertEqual(state.progress, 0.0)
    }

    func testProgressIsHalfAtHalfway() {
        let state = TimerState(config: .default, targetDuration: 100, remainingDuration: 50)
        XCTAssertEqual(state.progress, 0.5)
    }

    func testProgressIsOneWhenComplete() {
        let state = TimerState(config: .default, targetDuration: 100, remainingDuration: 0)
        XCTAssertEqual(state.progress, 1.0)
    }

    func testProgressHandlesZeroTargetDuration() {
        let state = TimerState(config: .default, targetDuration: 0, remainingDuration: 0)
        XCTAssertEqual(state.progress, 0.0)
    }

    func testIsCompleteFalseWhenStillRunning() {
        let state = TimerState(config: .default, targetDuration: 100, status: .running)
        XCTAssertFalse(state.isComplete)
    }

    func testIsCompleteTrueWhenStatusIsComplete() {
        let state = TimerState(config: .default, targetDuration: 100, status: .complete)
        XCTAssertTrue(state.isComplete)
    }

    func testIsCompleteTrueWhenStatusIsAlarm() {
        let state = TimerState(config: .default, targetDuration: 100, status: .alarm)
        XCTAssertTrue(state.isComplete)
    }

    func testTimeRemainingSeconds() {
        let state = TimerState(config: .default, targetDuration: 100, remainingDuration: 45.7)
        XCTAssertEqual(state.timeRemainingSeconds, 45)
    }

    func testStateDecodingSupportsLegacyKeysAndStatusNormalization() throws {
        let jsonString = """
        {
          "config": {},
          "target_duration": 120,
          "started_at": 1600000000,
          "remaining_duration": 60,
          "timerStatus": "PAUSED"
        }
        """
        let payload = Data(jsonString.utf8)

        let decoded = try JSONDecoder().decode(TimerState.self, from: payload)

        XCTAssertEqual(decoded.targetDuration, 120)
        XCTAssertEqual(decoded.startedAt.timeIntervalSince1970, 1600000000)
        XCTAssertEqual(decoded.remainingDuration, 60)
        XCTAssertEqual(decoded.status, .paused)
    }
}

final class TimerStatusTests: XCTestCase {

    func testStatusFromReturnsCompleteAtZero() {
        XCTAssertEqual(TimerStatus.from(remainingSeconds: 0, currentStatus: .running), .complete)
    }

    func testStatusFromReturnsCompleteWhenNegative() {
        XCTAssertEqual(TimerStatus.from(remainingSeconds: -5, currentStatus: .running), .complete)
    }

    func testStatusFromReturnsRunningAboveZero() {
        XCTAssertEqual(TimerStatus.from(remainingSeconds: 10, currentStatus: .running), .running)
    }

    func testStatusFromPreservesPaused() {
        XCTAssertEqual(TimerStatus.from(remainingSeconds: 10, currentStatus: .paused), .paused)
    }
}
