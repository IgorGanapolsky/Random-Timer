import XCTest
import Foundation
@testable import RandomTimer

// MARK: - Instrumented Mocks

/// MockNotificationServiceSpy records every call for delegation assertions.
@MainActor
final class MockNotificationServiceSpy: TimerNotificationHandling {
    var scheduleAlarmNotificationCallCount = 0
    var cancelPendingNotificationsCallCount = 0
    var playAlarmSoundCallCount = 0
    var stopAlarmSoundCallCount = 0
    var silenceAlarmCallCount = 0
    var startVibrationCallCount = 0
    var stopVibrationCallCount = 0
    var playPreviewSoundCallCount = 0
    var lastPreviewSoundType: SoundType?
    var lastPreviewVolume: Float?
    var updatePreviewVolumeCallCount = 0
    var lastUpdatedPreviewVolume: Float?
    var previewVolumeCallCount = 0
    var stopPreviewCallCount = 0
    var scheduleReengagementReminderCallCount = 0
    var cancelReengagementRemindersCallCount = 0
    var didTapAlarmNotification: Bool = false

    func requestNotificationPermission() async {}
    func scheduleAlarmNotification(at date: Date, soundType: SoundType) async { scheduleAlarmNotificationCallCount += 1 }
    func cancelPendingNotifications() async { cancelPendingNotificationsCallCount += 1 }
    func playAlarmSound(type: SoundType, volume: Float) { playAlarmSoundCallCount += 1 }
    func stopAlarmSound() { stopAlarmSoundCallCount += 1 }
    func silenceAlarm() { silenceAlarmCallCount += 1 }
    func startVibration() { startVibrationCallCount += 1 }
    func stopVibration() { stopVibrationCallCount += 1 }
    func playPreviewSound(type: SoundType, volume: Float) {
        playPreviewSoundCallCount += 1
        lastPreviewSoundType = type
        lastPreviewVolume = volume
    }
    func updatePreviewVolume(_ volume: Float) {
        updatePreviewVolumeCallCount += 1
        lastUpdatedPreviewVolume = volume
    }
    func previewVolume(type: SoundType, volume: Float) { previewVolumeCallCount += 1 }
    func stopPreview() { stopPreviewCallCount += 1 }
    func clearNotificationTapFlag() { didTapAlarmNotification = false }
    func scheduleReengagementReminder() { scheduleReengagementReminderCallCount += 1 }
    func cancelReengagementReminders() { cancelReengagementRemindersCallCount += 1 }
}

/// MockStorageSpy records save/clear calls for assertion.
final class MockStorageSpy: @unchecked Sendable, TimerStorage {
    var saveConfigCallCount = 0
    var saveTimerStateCallCount = 0
    var clearTimerStateCallCount = 0

    func saveConfig(_ config: TimerConfig) async { saveConfigCallCount += 1 }
    func loadConfig() async -> TimerConfig? { return nil }
    func saveTimerState(_ state: TimerState) async { saveTimerStateCallCount += 1 }
    func loadTimerState() async -> TimerState? { return nil }
    func clearTimerState() async { clearTimerStateCallCount += 1 }
    nonisolated func loadConfigSync() -> TimerConfig? { return nil }
    nonisolated func loadTimerStateSync() -> TimerState? { return nil }
    nonisolated func clearTimerStateSync() {}
}

// MARK: - Helpers

@MainActor
private func makeManager(
    storage: TimerStorage = MockStorageSpy(),
    notification: MockNotificationServiceSpy = MockNotificationServiceSpy(),
    liveActivity: MockLiveActivityService = MockLiveActivityService()
) -> TimerManager {
    TimerManager(
        storageService: storage,
        notificationService: notification,
        liveActivityService: liveActivity
    )
}

@MainActor
private func makeRunningState(
    duration: TimeInterval = 100,
    remaining: TimeInterval? = nil,
    config: TimerConfig = .default
) -> TimerState {
    TimerState(
        config: config,
        targetDuration: duration,
        remainingDuration: remaining ?? duration,
        status: .running
    )
}

@MainActor
private func makeAlarmState(
    config: TimerConfig = TimerConfig(minSeconds: 5, maxSeconds: 10, alarmDuration: 30),
    alarmTimeRemaining: TimeInterval = 25
) -> TimerState {
    TimerState(
        config: config,
        targetDuration: 5,
        remainingDuration: 0,
        status: .alarm,
        alarmTimeRemaining: alarmTimeRemaining,
        alarmStartedAt: Date()
    )
}

// MARK: - Initialization Tests

@MainActor
final class TimerManagerInitializationTests: XCTestCase {

    func testInitialTimerStateIsNil() {
        let manager = makeManager()
        XCTAssertNil(manager.timerState, "timerState must be nil on fresh init")
    }

    func testInitialIsAlarmSilencedIsFalse() {
        let manager = makeManager()
        XCTAssertFalse(manager.isAlarmSilenced, "isAlarmSilenced must be false on fresh init")
    }

    func testInitialConfigMatchesDefaultWhenStorageIsEmpty() {
        let manager = makeManager()
        XCTAssertEqual(manager.config, .default, "config must equal .default when storage returns nil")
    }

    func testInitWithStoredConfigLoadsIt() {
        final class StorageWithConfig: @unchecked Sendable, TimerStorage {
            func saveConfig(_ config: TimerConfig) async {}
            func loadConfig() async -> TimerConfig? { return nil }
            func saveTimerState(_ state: TimerState) async {}
            func loadTimerState() async -> TimerState? { return nil }
            func clearTimerState() async {}
            nonisolated func loadConfigSync() -> TimerConfig? {
                return TimerConfig(minSeconds: 10, maxSeconds: 120)
            }
            nonisolated func loadTimerStateSync() -> TimerState? { return nil }
            nonisolated func clearTimerStateSync() {}
        }
        let manager = TimerManager(
            storageService: StorageWithConfig(),
            notificationService: MockNotificationServiceSpy(),
            liveActivityService: MockLiveActivityService()
        )
        XCTAssertEqual(manager.config.minSeconds, 10)
        XCTAssertEqual(manager.config.maxSeconds, 120)
    }

    func testInitClearsAlarmOrCompleteStateFromPreviousSession() {
        for staleStatus in [TimerStatus.alarm, TimerStatus.complete] {
            final class StorageWithStaleState: @unchecked Sendable, TimerStorage {
                let status: TimerStatus
                var clearCalledSync = false
                init(status: TimerStatus) { self.status = status }
                func saveConfig(_ config: TimerConfig) async {}
                func loadConfig() async -> TimerConfig? { return nil }
                func saveTimerState(_ state: TimerState) async {}
                func loadTimerState() async -> TimerState? { return nil }
                func clearTimerState() async {}
                nonisolated func loadConfigSync() -> TimerConfig? { return nil }
                nonisolated func loadTimerStateSync() -> TimerState? {
                    return TimerState(config: .default, targetDuration: 10, status: status)
                }
                nonisolated func clearTimerStateSync() { clearCalledSync = true }
            }
            let storage = StorageWithStaleState(status: staleStatus)
            let manager = TimerManager(
                storageService: storage,
                notificationService: MockNotificationServiceSpy(),
                liveActivityService: MockLiveActivityService()
            )
            XCTAssertNil(manager.timerState, "Stale \(staleStatus) state must not restore on init")
            XCTAssertTrue(storage.clearCalledSync, "Stale \(staleStatus) state must be cleared from storage")
        }
    }
}

// MARK: - Start Timer Tests

@MainActor
final class TimerManagerStartTests: XCTestCase {

    func testStartTimerSetsRunningState() async {
        let manager = makeManager()
        await manager.startTimer()
        XCTAssertNotNil(manager.timerState)
        XCTAssertEqual(manager.timerState?.status, .running)
    }

    func testStartTimerResetsAlarmSilencedFlag() async {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager._setTimerStateForTesting(makeAlarmState())
        manager.silenceAlarm()
        XCTAssertTrue(manager.isAlarmSilenced)

        await manager.startTimer()

        XCTAssertFalse(manager.isAlarmSilenced, "startTimer must reset isAlarmSilenced to false")
    }

    func testStartTimerGeneratesDurationWithinConfiguredRange() async {
        let config = TimerConfig(minSeconds: 10, maxSeconds: 50)
        let manager = makeManager()
        manager.updateConfig(config)

        await manager.startTimer()

        guard let state = manager.timerState else {
            XCTFail("Expected timer state after start")
            return
        }
        XCTAssertGreaterThanOrEqual(state.targetDuration, Double(config.minSeconds))
        XCTAssertLessThanOrEqual(state.targetDuration, Double(config.maxSeconds))
    }

    func testStartTimerSchedulesAlarmNotification() async {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)

        await manager.startTimer()

        XCTAssertEqual(notification.scheduleAlarmNotificationCallCount, 1,
                       "startTimer must schedule exactly one alarm notification")
    }

    func testStartTimerStopsPreviewSound() async {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)

        await manager.startTimer()

        XCTAssertGreaterThanOrEqual(notification.stopPreviewCallCount, 1,
                                    "startTimer must stop any active preview sound")
    }
}

// MARK: - Pause / Resume Tests

@MainActor
final class TimerManagerPauseResumeTests: XCTestCase {

    func testPauseTimerTransitionsToPaused() {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeRunningState())

        manager.pauseTimer()

        XCTAssertEqual(manager.timerState?.status, .paused)
    }

    func testResumeTimerTransitionsToRunning() {
        let manager = makeManager()
        var state = makeRunningState()
        state.status = .paused
        manager._setTimerStateForTesting(state)

        manager.resumeTimer()

        XCTAssertEqual(manager.timerState?.status, .running)
    }

    func testPauseIsIdempotentOnAlreadyPausedTimer() {
        let manager = makeManager()
        var state = makeRunningState()
        state.status = .paused
        manager._setTimerStateForTesting(state)

        manager.pauseTimer()

        XCTAssertEqual(manager.timerState?.status, .paused, "Pausing already-paused timer must be a no-op")
    }

    func testResumeDoesNothingWhenTimerIsRunning() {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeRunningState())

        manager.resumeTimer()

        XCTAssertEqual(manager.timerState?.status, .running,
                       "resumeTimer on already-running timer must be a no-op")
    }

    func testPauseAndResumePreservesRemainingDuration() {
        let manager = makeManager()
        let state = makeRunningState(duration: 120, remaining: 75)
        manager._setTimerStateForTesting(state)

        manager.pauseTimer()
        manager.resumeTimer()

        XCTAssertEqual(manager.timerState?.remainingDuration, 75,
                       "Pause/resume cycle must preserve remainingDuration")
    }

}

// MARK: - Cancel Timer Tests

@MainActor
final class TimerManagerCancelTests: XCTestCase {

    func testCancelTimerClearsTimerState() async {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeRunningState())

        await manager.cancelTimer()

        XCTAssertNil(manager.timerState, "cancelTimer must set timerState to nil")
    }

    func testCancelTimerCancelsPendingNotifications() async {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager._setTimerStateForTesting(makeRunningState())

        await manager.cancelTimer()

        XCTAssertGreaterThanOrEqual(notification.cancelPendingNotificationsCallCount, 1,
                                    "cancelTimer must cancel pending notifications")
    }

    func testCancelTimerClearsStorage() async {
        let storage = MockStorageSpy()
        let manager = makeManager(storage: storage)
        manager._setTimerStateForTesting(makeRunningState())

        await manager.cancelTimer()

        XCTAssertGreaterThanOrEqual(storage.clearTimerStateCallCount, 1,
                                    "cancelTimer must clear timer state from storage")
    }
}

// MARK: - Dismiss Alarm Tests

@MainActor
final class TimerManagerDismissAlarmTests: XCTestCase {

    func testDismissAlarmClearsTimerState() async {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeAlarmState())

        await manager.dismissAlarm()

        XCTAssertNil(manager.timerState, "dismissAlarm must clear timerState")
    }

    func testDismissAlarmWhenNotSilencedLeavesIsAlarmSilencedFalse() async {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeAlarmState())

        await manager.dismissAlarm()

        XCTAssertFalse(manager.isAlarmSilenced)
    }

    func testDismissAlarmStopsAlarmSoundAndVibration() async {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager._setTimerStateForTesting(makeAlarmState())

        await manager.dismissAlarm()

        XCTAssertGreaterThanOrEqual(notification.stopAlarmSoundCallCount, 1, "dismissAlarm must stop alarm sound")
        XCTAssertGreaterThanOrEqual(notification.stopVibrationCallCount, 1, "dismissAlarm must stop vibration")
    }

    func testDismissAlarmSchedulesReengagementReminder() async {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager._setTimerStateForTesting(makeAlarmState())

        await manager.dismissAlarm()

        XCTAssertGreaterThanOrEqual(notification.scheduleReengagementReminderCallCount, 1,
                                    "dismissAlarm must schedule re-engagement reminder")
    }
}

// MARK: - Silence Alarm Tests

@MainActor
final class TimerManagerAlarmSilenceTests: XCTestCase {

    func testSilenceAlarmSetsFlag() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager._setTimerStateForTesting(makeAlarmState())

        manager.silenceAlarm()

        XCTAssertTrue(manager.isAlarmSilenced)
    }

    func testSilenceAlarmCallsNotificationSilence() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager._setTimerStateForTesting(makeAlarmState())

        manager.silenceAlarm()

        XCTAssertEqual(notification.silenceAlarmCallCount, 1,
                       "silenceAlarm must delegate to notification service")
    }

    func testSilenceAlarmPreservesTimerState() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager._setTimerStateForTesting(makeAlarmState(alarmTimeRemaining: 20))

        manager.silenceAlarm()

        XCTAssertEqual(manager.timerState?.status, .alarm, "silenceAlarm must not change timer status")
        XCTAssertNotNil(manager.timerState, "silenceAlarm must not clear timerState")
    }

    func testSilenceAlarmNoOpWhenNotInAlarmState() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager._setTimerStateForTesting(makeRunningState())

        manager.silenceAlarm()

        XCTAssertFalse(manager.isAlarmSilenced)
        XCTAssertEqual(notification.silenceAlarmCallCount, 0)
    }

    func testSilenceAlarmNoOpWhenTimerStateIsNil() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)

        manager.silenceAlarm()

        XCTAssertFalse(manager.isAlarmSilenced)
        XCTAssertEqual(notification.silenceAlarmCallCount, 0)
    }
}

// MARK: - Update Config Tests

@MainActor
final class TimerManagerUpdateConfigTests: XCTestCase {

    func testUpdateConfigStoresNewConfig() {
        let manager = makeManager()
        let newConfig = TimerConfig(minSeconds: 15, maxSeconds: 60)

        manager.updateConfig(newConfig)

        XCTAssertEqual(manager.config, newConfig)
    }

    func testUpdateConfigPropagatesIntoRunningTimerState() {
        let manager = makeManager()
        let initialConfig = TimerConfig(minSeconds: 0, maxSeconds: 30, repeatEnabled: false)
        manager._setTimerStateForTesting(makeRunningState(config: initialConfig))

        let updatedConfig = TimerConfig(minSeconds: 0, maxSeconds: 30, repeatEnabled: true)
        manager.updateConfig(updatedConfig)

        XCTAssertTrue(manager.timerState?.config.repeatEnabled ?? false,
                      "updateConfig must sync new config into running timer state")
    }

    func testUpdateConfigDoesNotCrashWhenNoTimer() {
        let manager = makeManager()
        let newConfig = TimerConfig(minSeconds: 5, maxSeconds: 25)
        manager.updateConfig(newConfig)
        XCTAssertEqual(manager.config, newConfig)
        XCTAssertNil(manager.timerState)
    }

    func testUpdateConfigSavesToStorage() async {
        let storage = MockStorageSpy()
        let manager = makeManager(storage: storage)
        manager.updateConfig(TimerConfig(minSeconds: 10, maxSeconds: 120))

        try? await Task.sleep(for: .milliseconds(100))

        XCTAssertGreaterThanOrEqual(storage.saveConfigCallCount, 1,
                                    "updateConfig must persist config to storage")
    }

}

// MARK: - Reset Timer Tests

@MainActor
final class TimerManagerResetTests: XCTestCase {

    func testResetTimerDoesNothingWhenNoTimerState() async {
        let manager = makeManager()
        await manager.resetTimer()
        XCTAssertNil(manager.timerState, "resetTimer must be a no-op when timerState is nil")
    }

    func testResetTimerProducesNewStateWithinRange() async {
        let manager = makeManager(
            storage: MockStorageSpy(),
            notification: MockNotificationServiceSpy(),
            liveActivity: MockLiveActivityService()
        )
        let config = TimerConfig(minSeconds: 5, maxSeconds: 30)
        manager._setTimerStateForTesting(
            TimerState(config: config, targetDuration: 20, remainingDuration: 10, status: .running)
        )

        await manager.resetTimer()

        guard let rerolled = manager.timerState else {
            XCTFail("Expected timer state after reset"); return
        }
        XCTAssertGreaterThanOrEqual(rerolled.targetDuration, Double(config.minSeconds))
        XCTAssertLessThanOrEqual(rerolled.targetDuration, Double(config.maxSeconds))
    }

    func testResetTimerSetsRemainingDurationEqualToTargetDuration() async {
        let manager = makeManager(
            storage: MockStorageSpy(),
            notification: MockNotificationServiceSpy(),
            liveActivity: MockLiveActivityService()
        )
        manager._setTimerStateForTesting(
            TimerState(config: TimerConfig(minSeconds: 5, maxSeconds: 20),
                       targetDuration: 20, remainingDuration: 5, status: .running)
        )

        await manager.resetTimer()

        guard let rerolled = manager.timerState else {
            XCTFail("Expected timer state after reset"); return
        }
        XCTAssertEqual(rerolled.remainingDuration, rerolled.targetDuration, accuracy: 0.001,
                       "Reset timer must have remainingDuration == targetDuration")
    }

    func testResetTimerResetsAlarmSilencedFlag() async {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(
            storage: MockStorageSpy(),
            notification: notification,
            liveActivity: MockLiveActivityService()
        )
        manager._setTimerStateForTesting(makeAlarmState())
        manager.silenceAlarm()
        XCTAssertTrue(manager.isAlarmSilenced)

        await manager.resetTimer()

        XCTAssertFalse(manager.isAlarmSilenced, "resetTimer must clear isAlarmSilenced flag")
    }

    func testResetTimerSchedulesNewNotification() async {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(
            storage: MockStorageSpy(),
            notification: notification,
            liveActivity: MockLiveActivityService()
        )
        manager._setTimerStateForTesting(makeRunningState())

        await manager.resetTimer()

        XCTAssertGreaterThanOrEqual(notification.scheduleAlarmNotificationCallCount, 1,
                                    "resetTimer must schedule a new alarm notification")
    }
}

// MARK: - Preview Sound Tests

@MainActor
final class TimerManagerPreviewSoundTests: XCTestCase {

    func testPreviewSoundDelegatesToNotificationServiceWithCurrentConfig() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager.updateConfig(TimerConfig(minSeconds: 0, maxSeconds: 30, soundType: .gentle, volume: 0.7))

        manager.previewSound()

        XCTAssertEqual(notification.playPreviewSoundCallCount, 1)
        XCTAssertEqual(notification.lastPreviewSoundType, .gentle)
        XCTAssertEqual(notification.lastPreviewVolume ?? 0, 0.7, accuracy: 0.001)
    }

    func testPreviewSoundWithExplicitTypeOverridesCurrentConfigType() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager.updateConfig(TimerConfig(minSeconds: 0, maxSeconds: 30, soundType: .intense, volume: 0.5))

        manager.previewSound(type: .gentle)

        XCTAssertEqual(notification.lastPreviewSoundType, .gentle,
                       "previewSound(type:) must pass the explicit type")
        XCTAssertEqual(notification.lastPreviewVolume ?? 0, 0.5, accuracy: 0.001,
                       "previewSound(type:) must use the current config volume")
    }

    func testUpdatePreviewVolumeDelegatesToNotificationService() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager.updateConfig(TimerConfig(minSeconds: 0, maxSeconds: 30, volume: 0.6))

        manager.updatePreviewVolume()

        XCTAssertEqual(notification.updatePreviewVolumeCallCount, 1)
        XCTAssertEqual(notification.lastUpdatedPreviewVolume ?? 0, 0.6, accuracy: 0.001)
    }

    func testPreviewVolumeDelegatesToNotificationService() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)

        manager.previewVolume()

        XCTAssertEqual(notification.previewVolumeCallCount, 1)
    }
}

// MARK: - Handle Background Tests

@MainActor
final class TimerManagerHandleBackgroundTests: XCTestCase {

    func testHandleBackgroundSilencesAlarmWhenInAlarmState() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager._setTimerStateForTesting(makeAlarmState())

        manager.handleBackground()

        XCTAssertTrue(manager.isAlarmSilenced,
                      "handleBackground must silence alarm when status is .alarm")
    }

    func testHandleBackgroundIsNoOpWhenInRunningState() {
        let notification = MockNotificationServiceSpy()
        let manager = makeManager(notification: notification)
        manager._setTimerStateForTesting(makeRunningState())

        manager.handleBackground()

        XCTAssertFalse(manager.isAlarmSilenced)
        XCTAssertEqual(notification.silenceAlarmCallCount, 0)
    }

    func testHandleBackgroundPreservesAlarmStatus() {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeAlarmState())

        manager.handleBackground()

        XCTAssertEqual(manager.timerState?.status, .alarm,
                       "handleBackground must preserve .alarm status")
    }
}

// MARK: - Process Pending Live Activity Action Tests

@MainActor
final class TimerManagerLiveActivityActionTests: XCTestCase {

    private let appGroupSuite = timerAppGroupSuite
    private let pendingKey = timerPendingActionKey

    override func setUp() {
        super.setUp()
        UserDefaults(suiteName: appGroupSuite)?.removeObject(forKey: pendingKey)
    }

    override func tearDown() {
        super.tearDown()
        UserDefaults(suiteName: appGroupSuite)?.removeObject(forKey: pendingKey)
    }

    func testProcessPendingActionPausesTimerWhenPauseActionSet() async {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeRunningState())

        UserDefaults(suiteName: appGroupSuite)?.set(TimerAction.pause.rawValue, forKey: pendingKey)
        await manager.processPendingLiveActivityAction()

        XCTAssertEqual(manager.timerState?.status, .paused,
                       "processPendingLiveActivityAction must pause timer when action is .pause")
    }

    func testProcessPendingActionResumesTimerWhenResumeActionSet() async {
        let manager = makeManager()
        var state = makeRunningState()
        state.status = .paused
        manager._setTimerStateForTesting(state)

        UserDefaults(suiteName: appGroupSuite)?.set(TimerAction.resume.rawValue, forKey: pendingKey)
        await manager.processPendingLiveActivityAction()

        XCTAssertEqual(manager.timerState?.status, .running,
                       "processPendingLiveActivityAction must resume timer when action is .resume")
    }

    func testProcessPendingActionCancelsTimerWhenStopActionSetAndNotAlarming() async {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeRunningState())

        UserDefaults(suiteName: appGroupSuite)?.set(TimerAction.stop.rawValue, forKey: pendingKey)
        await manager.processPendingLiveActivityAction()

        XCTAssertNil(manager.timerState,
                     "processPendingLiveActivityAction must cancel timer when action is .stop")
    }

    func testProcessPendingActionClearsKeyAfterProcessing() async {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeRunningState())

        UserDefaults(suiteName: appGroupSuite)?.set(TimerAction.pause.rawValue, forKey: pendingKey)
        await manager.processPendingLiveActivityAction()

        let remaining = UserDefaults(suiteName: appGroupSuite)?.string(forKey: pendingKey)
        XCTAssertNil(remaining, "processPendingLiveActivityAction must clear the pending action key")
    }

    func testProcessPendingActionIsNoOpWhenNoPendingAction() async {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeRunningState())

        await manager.processPendingLiveActivityAction()

        XCTAssertEqual(manager.timerState?.status, .running)
    }
}

// MARK: - Edge Case Tests

@MainActor
final class TimerManagerEdgeCaseTests: XCTestCase {

    func testRapidPauseResumeDoesNotCrash() {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeRunningState())

        for _ in 0..<20 {
            manager.pauseTimer()
            manager.resumeTimer()
        }

        XCTAssertNotNil(manager.timerState)
    }

    func testConfigRemainsAfterCancel() async {
        let manager = makeManager()
        let config = TimerConfig(minSeconds: 5, maxSeconds: 60)
        manager.updateConfig(config)
        manager._setTimerStateForTesting(makeRunningState())

        await manager.cancelTimer()

        XCTAssertEqual(manager.config, config, "Config must be preserved after cancelTimer")
    }

    func testMultipleUpdateConfigCallsApplyLastValue() {
        let manager = makeManager()

        manager.updateConfig(TimerConfig(minSeconds: 0, maxSeconds: 30))
        manager.updateConfig(TimerConfig(minSeconds: 5, maxSeconds: 60))
        manager.updateConfig(TimerConfig(minSeconds: 10, maxSeconds: 120))

        XCTAssertEqual(manager.config.minSeconds, 10)
        XCTAssertEqual(manager.config.maxSeconds, 120)
    }

    func testSilenceAfterDismissDoesNotCrash() async {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeAlarmState())

        await manager.dismissAlarm()
        manager.silenceAlarm()

        XCTAssertNil(manager.timerState)
        XCTAssertFalse(manager.isAlarmSilenced)
    }

    func testPauseAfterCancelDoesNotCrash() async {
        let manager = makeManager()
        manager._setTimerStateForTesting(makeRunningState())

        await manager.cancelTimer()
        manager.pauseTimer()

        XCTAssertNil(manager.timerState)
    }
}
