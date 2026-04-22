import XCTest
@testable import RandomTimer

final class TimerManagerStartupPlanTests: XCTestCase {
    private func makeConfig(
        minSeconds: Int = 5,
        maxSeconds: Int = 300,
        useExtendedRange: Bool = false
    ) -> RandomTimer.TimerConfig {
        RandomTimer.TimerConfig(
            minSeconds: minSeconds,
            maxSeconds: maxSeconds,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false,
            useExtendedRange: useExtendedRange
        )
    }

    private func makeState(status: RandomTimer.TimerStatus) -> RandomTimer.TimerState {
        RandomTimer.TimerState(
            config: makeConfig(),
            targetDuration: 30,
            startedAt: Date(),
            remainingDuration: 10,
            status: status
        )
    }

    func testResolveUsesDefaultConfigWhenNothingPersisted() {
        let plan = TimerManagerStartupPlan.resolve(
            rawConfig: nil,
            persistedTimerState: nil,
            isPro: false
        )

        XCTAssertEqual(plan.initialConfig.minSeconds, RandomTimer.TimerConfig.default.minSeconds)
        XCTAssertEqual(plan.initialConfig.maxSeconds, RandomTimer.TimerConfig.default.maxSeconds)
        XCTAssertFalse(plan.shouldClearPersistedTimerState)
        XCTAssertFalse(plan.shouldRestoreActiveTimer)
    }

    func testResolveClearsPersistedAlarmState() {
        let plan = TimerManagerStartupPlan.resolve(
            rawConfig: makeConfig(),
            persistedTimerState: makeState(status: .alarm),
            isPro: false
        )

        XCTAssertTrue(plan.shouldClearPersistedTimerState)
        XCTAssertFalse(plan.shouldRestoreActiveTimer)
    }

    func testResolveClearsPersistedCompleteState() {
        let plan = TimerManagerStartupPlan.resolve(
            rawConfig: makeConfig(),
            persistedTimerState: makeState(status: .complete),
            isPro: false
        )

        XCTAssertTrue(plan.shouldClearPersistedTimerState)
        XCTAssertFalse(plan.shouldRestoreActiveTimer)
    }

    func testResolveRestoresPersistedRunningState() {
        let plan = TimerManagerStartupPlan.resolve(
            rawConfig: makeConfig(),
            persistedTimerState: makeState(status: .running),
            isPro: false
        )

        XCTAssertFalse(plan.shouldClearPersistedTimerState)
        XCTAssertTrue(plan.shouldRestoreActiveTimer)
    }

    func testResolveClampsProOnlyRangeForFreeUsers() {
        let plan = TimerManagerStartupPlan.resolve(
            rawConfig: makeConfig(minSeconds: 5, maxSeconds: 3600, useExtendedRange: true),
            persistedTimerState: nil,
            isPro: false
        )

        XCTAssertEqual(plan.initialConfig.maxSeconds, RandomTimer.TimerConfig.maxSecondsFree)
        XCTAssertFalse(plan.initialConfig.useExtendedRange)
    }
}
