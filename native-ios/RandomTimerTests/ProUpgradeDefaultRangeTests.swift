import XCTest
@testable import RandomTimer

final class ProUpgradeDefaultRangeTests: XCTestCase {

    @MainActor
    func testEnableExtendedRangeDefaultForNewProUnlockPreservesRawProValues() async {
        let rawConfig = RandomTimer.TimerConfig(
            minSeconds: 30,
            maxSeconds: 900,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: RandomTimer.SoundType.bell,
            volume: 0.5,
            vibrationEnabled: false,
            useExtendedRange: false,
            voiceEnabled: true,
            repeatRounds: 0
        )
        let storage = InMemoryTimerStorage(config: rawConfig)
        let manager = TimerManager(
            storageService: storage,
            notificationService: NoopNotificationService(),
            liveActivityService: NoopLiveActivityService()
        )

        manager.enableExtendedRangeDefaultForNewProUnlock(isPro: true)
        try? await Task.sleep(nanoseconds: 50_000_000)

        let savedConfig = await storage.loadConfig()
        XCTAssertEqual(savedConfig?.maxSeconds, 900)
        XCTAssertEqual(savedConfig?.soundType, .bell)
        XCTAssertTrue(savedConfig?.useExtendedRange == true)
        XCTAssertEqual(manager.config.maxSeconds, 900)
        XCTAssertEqual(manager.config.soundType, .bell)
        XCTAssertTrue(manager.config.useExtendedRange)
    }
}

private final class InMemoryTimerStorage: TimerStorage, @unchecked Sendable {
    private var config: RandomTimer.TimerConfig?
    private var timerState: RandomTimer.TimerState?

    init(
        config: RandomTimer.TimerConfig? = nil,
        timerState: RandomTimer.TimerState? = nil
    ) {
        self.config = config
        self.timerState = timerState
    }

    func saveConfig(_ config: RandomTimer.TimerConfig) async {
        self.config = config
    }

    func loadConfig() async -> RandomTimer.TimerConfig? {
        config
    }

    func saveTimerState(_ state: RandomTimer.TimerState) async {
        timerState = state
    }

    func loadTimerState() async -> RandomTimer.TimerState? {
        timerState
    }

    func clearTimerState() async {
        timerState = nil
    }

    func loadConfigSync() -> RandomTimer.TimerConfig? {
        config
    }

    func loadTimerStateSync() -> RandomTimer.TimerState? {
        timerState
    }

    func clearTimerStateSync() {
        timerState = nil
    }
}

@MainActor
private final class NoopNotificationService: TimerNotificationHandling {
    var didTapAlarmNotification: Bool = false

    func requestNotificationPermission() async {}
    func scheduleAlarmNotification(at date: Date, soundType: RandomTimer.SoundType) async {}
    func cancelPendingNotifications() async {}
    func playAlarmSound(type: RandomTimer.SoundType, volume: Float) {}
    func stopAlarmSound() {}
    func silenceAlarm() {}
    func startVibration() {}
    func stopVibration() {}
    func playPreviewSound(type: RandomTimer.SoundType, volume: Float) {}
    func updatePreviewVolume(_ volume: Float) {}
    func previewVolume(type: RandomTimer.SoundType, volume: Float) {}
    func stopPreview() {}
    func clearNotificationTapFlag() {}
    func scheduleReengagementReminder() {}
    func cancelReengagementReminders() {}
}

@MainActor
private final class NoopLiveActivityService: TimerLiveActivityHandling {
    func start(state: RandomTimer.TimerState) async {}
    func update(state: RandomTimer.TimerState) async {}
    func end() async {}
    func endAll() async {}
}
