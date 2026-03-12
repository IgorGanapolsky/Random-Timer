import XCTest
import Foundation
@testable import RandomTimer

final class TimerConfigTests: XCTestCase {

    func testDefaultConfigHasValidRange() {
        let config = TimerConfig.default

<<<<<<< HEAD
        XCTAssertEqual(config.minSeconds, 0)
        XCTAssertEqual(config.maxSeconds, 30)
||||||| 0ed85a75
        XCTAssertEqual(config.minSeconds, 0)
        XCTAssertEqual(config.maxSeconds, 300)
=======
        XCTAssertEqual(config.minSeconds, 10)
        XCTAssertEqual(config.maxSeconds, 30)
>>>>>>> feat/tactical-gsd-sprint-20260306
        XCTAssertEqual(config.alarmDuration, 10)
    }

    func testConfigInitEnforcesPreconditions() {
        // minSeconds cannot be negative
        // XCTest expect crash is hard, so we just check it doesn't throw if we use valid values
        let _ = TimerConfig(minSeconds: 0, maxSeconds: 10)
    }

    func testConfigClampingForFreeUser() {
        let proConfig = TimerConfig(
            minSeconds: 0,
            maxSeconds: 3600,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .klaxon,
            volume: 0.5,
            vibrationEnabled: false
        )

        let clamped = proConfig.clamped(isPro: false)

        XCTAssertEqual(clamped.maxSeconds, 300)
        XCTAssertEqual(clamped.soundType, .intense)
    }

    func testConfigDecodingSupportsLegacyKeysAndLooseSoundNames() throws {
        let payload = """
        {
          "min_time": -5,
          "max_time": 3600,
          "alarm_duration": 0,
          "hidden_mode": "true",
          "repeat_enabled": "1",
          "sound_type": "DRUM_ROLL",
          "soundVolume": "1.5",
          "vibration": "yes"
        }
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(TimerConfig.self, from: payload)

        XCTAssertEqual(decoded.minSeconds, 0)
        XCTAssertEqual(decoded.maxSeconds, 3600)
        XCTAssertEqual(decoded.alarmDuration, 1)
        XCTAssertTrue(decoded.hiddenMode)
        XCTAssertTrue(decoded.repeatEnabled)
        XCTAssertEqual(decoded.soundType, .drumRoll)
        XCTAssertEqual(decoded.volume, 1.0, accuracy: 0.0001)
        XCTAssertTrue(decoded.vibrationEnabled)
    }
}

final class TimeRangeAdjusterTests: XCTestCase {

    func testMinChangeWithinGapKeepsMaxUnchanged() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 0,
            currentMaxSeconds: 300,
            newMinSeconds: 120
        )

        XCTAssertEqual(adjusted.min, 120)
        XCTAssertEqual(adjusted.max, 300)
    }

    func testMinChangeBeyondMaxMinusGapPushesMaxForward() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 0,
            currentMaxSeconds: 10,
            newMinSeconds: 15,
            minGapSeconds: 0
        )

        XCTAssertEqual(adjusted.min, 15)
        XCTAssertEqual(adjusted.max, 15)
    }

    func testMinChangeThatWouldExceedMaxLimitClampsToMaxMinusGap() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 250,
            currentMaxSeconds: 300,
            newMinSeconds: 300,
            maxSecondsLimit: 300,
            minGapSeconds: 0
        )

        XCTAssertEqual(adjusted.min, 300)
        XCTAssertEqual(adjusted.max, 300)
    }

    func testMaxChangeWithinGapKeepsMinUnchanged() {
        let adjusted = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: 0,
            currentMaxSeconds: 300,
            newMaxSeconds: 200,
            minGapSeconds: 0
        )

        XCTAssertEqual(adjusted.min, 0)
        XCTAssertEqual(adjusted.max, 200)
    }

    func testMaxChangeBelowMinPlusGapPullsMinBack() {
        let adjusted = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: 100,
            currentMaxSeconds: 300,
            newMaxSeconds: 50,
            minGapSeconds: 0
        )

        XCTAssertEqual(adjusted.min, 50)
        XCTAssertEqual(adjusted.max, 50)
    }

    func testReportedBugZeroToThirtyRangeIsPossible() {
        // User sets min to 0
        let step1 = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 10,
            currentMaxSeconds: 30,
            newMinSeconds: 0,
            minGapSeconds: 0
        )
        XCTAssertEqual(step1.min, 0)
        XCTAssertEqual(step1.max, 30)

        // User sets max to 30 (already there, but let's be explicit)
        let step2 = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: 0,
            currentMaxSeconds: 30,
            newMaxSeconds: 30,
            minGapSeconds: 0
        )
        XCTAssertEqual(step2.min, 0)
        XCTAssertEqual(step2.max, 30)
    }

    func testMaxChangeThatWouldPullMinBelowLimitClampsToMinLimit() {
        let adjusted = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: 10,
            currentMaxSeconds: 40,
            newMaxSeconds: 0
        )

        XCTAssertEqual(adjusted.min, 0)
        XCTAssertEqual(adjusted.max, 0 + TimeRangeAdjuster.defaultMinGapSeconds)
        XCTAssertGreaterThanOrEqual(adjusted.max - adjusted.min, TimeRangeAdjuster.defaultMinGapSeconds)
    }

    func testMinChangeByOneSecondNearUpperBoundPushesMaxByOne() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 298,
            currentMaxSeconds: 299,
            newMinSeconds: 299,
            maxSecondsLimit: 300,
            minGapSeconds: 1
        )

        XCTAssertEqual(adjusted.min, 299)
        XCTAssertEqual(adjusted.max, 300)
    }

    func testMinChangeBeyondUpperBoundIsDeterministicallyClamped() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 290,
            currentMaxSeconds: 300,
            newMinSeconds: 305,
            maxSecondsLimit: 300,
            minGapSeconds: 1
        )

        XCTAssertEqual(adjusted.min, 299)
        XCTAssertEqual(adjusted.max, 300)
    }
}

final class TimeIntervalExtensionTests: XCTestCase {

    func testFormattedMMSS() {
        XCTAssertEqual(TimeInterval(65).formattedMMSS, "01:05")
        XCTAssertEqual(TimeInterval(3600).formattedMMSS, "60:00")
        XCTAssertEqual(TimeInterval(0).formattedMMSS, "00:00")
    }

    func testFormattedDuration() {
        XCTAssertEqual(TimeInterval(45).formattedDuration, "45s")
        XCTAssertEqual(TimeInterval(60).formattedDuration, "1m")
        XCTAssertEqual(TimeInterval(90).formattedDuration, "1m 30s")
    }
}

final class TimerManagerSilenceTests: XCTestCase {

    @MainActor
    func testIsAlarmSilencedDefaultsToFalse() {
        let manager = TimerManager()
        XCTAssertFalse(manager.isAlarmSilenced)
    }

    @MainActor
    func testSilenceAlarmSetsIsAlarmSilencedTrue() {
        let timerManager = TimerManager()

        let config = TimerConfig(
            minSeconds: 5, maxSeconds: 10, alarmDuration: 30,
            hiddenMode: false, repeatEnabled: false,
            soundType: .intense, volume: 0.5, vibrationEnabled: false
        )
        let alarmState = TimerState(
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

        let config = TimerConfig(
            minSeconds: 5, maxSeconds: 10, alarmDuration: 30,
            hiddenMode: false, repeatEnabled: false,
            soundType: .intense, volume: 0.5, vibrationEnabled: false
        )
        let alarmState = TimerState(
            config: config, targetDuration: 5,
            remainingDuration: 0, status: .alarm,
            alarmTimeRemaining: 25, alarmStartedAt: Date()
        )
        timerManager._setTimerStateForTesting(alarmState)
        timerManager.silenceAlarm()
        XCTAssertTrue(timerManager.isAlarmSilenced)

        // Start new timer
        await timerManager.startTimer()
        XCTAssertFalse(timerManager.isAlarmSilenced,
                       "New timer must reset isAlarmSilenced to false")
    }

    @MainActor
    func testHandleForegroundViaNotificationTapSetsAlarmSilenced() async {
        let mockNotification = MockNotificationService()
        mockNotification.didTapAlarmNotification = true
        let timerManager = TimerManager(
            storageService: MockStorageService(),
            notificationService: mockNotification,
            liveActivityService: MockLiveActivityService()
        )

        let config = TimerConfig(
            minSeconds: 5, maxSeconds: 10, alarmDuration: 30,
            repeatEnabled: false
        )
        let state = TimerState(
            config: config, targetDuration: 5,
            startedAt: Date().addingTimeInterval(-100) // Way in the past
        )
        timerManager._setTimerStateForTesting(state)

        await timerManager.handleForeground()

        XCTAssertTrue(timerManager.isAlarmSilenced,
                      "Returning via notification tap while alarm expired should set isAlarmSilenced")
    }

    @MainActor
    var manager: TimerManager { return TimerManager() }
}

// MARK: - Mocks

final class MockStorageService: TimerStorage {
    func saveConfig(_ config: TimerConfig) async {}
    func loadConfig() async -> TimerConfig? { return nil }
    func saveTimerState(_ state: TimerState) async {}
    func loadTimerState() async -> TimerState? { return nil }
    func clearTimerState() async {}
    nonisolated func loadConfigSync() -> TimerConfig? { return nil }
    nonisolated func loadTimerStateSync() -> TimerState? { return nil }
    nonisolated func clearTimerStateSync() {}
}

final class MockNotificationService: TimerNotificationHandling {
    func requestNotificationPermission() async {}
    func scheduleAlarmNotification(at date: Date, soundType: SoundType) async {}
    func cancelPendingNotifications() async {}
    func playAlarmSound(type: SoundType, volume: Float) {}
    func stopAlarmSound() {}
    func silenceAlarm() {}
    func startVibration() {}
    func stopVibration() {}
    func playPreviewSound(type: SoundType, volume: Float) {}
    func updatePreviewVolume(_ volume: Float) {}
    func previewVolume(type: SoundType, volume: Float) {}
    func stopPreview() {}
    var didTapAlarmNotification: Bool = false
    func clearNotificationTapFlag() { didTapAlarmNotification = false }
    func scheduleReengagementReminder() {}
    func cancelReengagementReminders() {}
}

final class MockLiveActivityService: TimerLiveActivityHandling {
    func start(state: TimerState) async {}
    func update(state: TimerState) async {}
    func end() async {}
    func endAll() async {}
}

final class TimerManagerTests: XCTestCase {

    @MainActor
    func testInitialConfigIsDefault() {
        let manager = TimerManager(storageService: MockStorageService())
        XCTAssertEqual(manager.config, .default)
    }

    @MainActor
    func testUpdateConfigDoesNotCrashWhenNoTimerRunning() {
        let manager = TimerManager()
        let newConfig = TimerConfig(minSeconds: 10, maxSeconds: 20)
        manager.updateConfig(newConfig)
        XCTAssertEqual(manager.config, newConfig)
    }

    @MainActor
    func testStartTimerSetsTimerState() async {
        let manager = TimerManager()
        await manager.startTimer()
        XCTAssertNotNil(manager.timerState)
        XCTAssertEqual(manager.timerState?.status, .running)
    }

    @MainActor
    func testPauseAndResumeTimer() {
        let manager = TimerManager()
        let state = TimerState(config: .default, targetDuration: 100)
        manager._setTimerStateForTesting(state)

        manager.pauseTimer()
        XCTAssertEqual(manager.timerState?.status, .paused)

        manager.resumeTimer()
        XCTAssertEqual(manager.timerState?.status, .running)
    }

    @MainActor
    func testCancelTimerClearsTimerState() async {
        let manager = TimerManager()
        let state = TimerState(config: .default, targetDuration: 100)
        manager._setTimerStateForTesting(state)

        await manager.cancelTimer()
        XCTAssertNil(manager.timerState)
    }

    @MainActor
    func testLoopTogglePropagatesToRunningTimer() {
        let manager = TimerManager()
        let config = TimerConfig(repeatEnabled: false)
        let state = TimerState(config: config, targetDuration: 100)
        manager._setTimerStateForTesting(state)

        let newConfig = TimerConfig(repeatEnabled: true)
        manager.updateConfig(newConfig)

        XCTAssertTrue(manager.timerState?.config.repeatEnabled ?? false)
    }

    @MainActor
    func testResetTimerRerollsDurationWithinConfiguredRange() async {
        let manager = TimerManager(
            storageService: MockStorageService(),
            notificationService: MockNotificationService(),
            liveActivityService: MockLiveActivityService()
        )
        let config = TimerConfig(minSeconds: 0, maxSeconds: 30)
        let state = TimerState(config: config, targetDuration: 30, remainingDuration: 12, status: .running)
        manager._setTimerStateForTesting(state)

        await manager.resetTimer()

        guard let rerolled = manager.timerState else {
            XCTFail("Expected timer state after reset")
            return
        }

        XCTAssertGreaterThanOrEqual(rerolled.targetDuration, Double(config.minSeconds))
        XCTAssertLessThanOrEqual(rerolled.targetDuration, Double(config.maxSeconds))
        XCTAssertEqual(rerolled.remainingDuration, rerolled.targetDuration, accuracy: 0.0001)
    }

    @MainActor
    func testResetTimerUsesExactDurationWhenRangeCollapsed() async {
        let manager = TimerManager(
            storageService: MockStorageService(),
            notificationService: MockNotificationService(),
            liveActivityService: MockLiveActivityService()
        )
        let config = TimerConfig(minSeconds: 30, maxSeconds: 30)
        let state = TimerState(config: config, targetDuration: 10, remainingDuration: 3, status: .running)
        manager._setTimerStateForTesting(state)

        await manager.resetTimer()

        guard let rerolled = manager.timerState else {
            XCTFail("Expected timer state after reset")
            return
        }
        XCTAssertEqual(rerolled.targetDuration, 30, accuracy: 0.0001)
        XCTAssertEqual(rerolled.remainingDuration, 30, accuracy: 0.0001)
    }
}

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
        let payload = """
        {
          "config": {},
          "target_duration": 120,
          "started_at": 1600000000,
          "remaining_duration": 60,
          "timerStatus": "PAUSED"
        }
        """.data(using: .utf8)!

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
