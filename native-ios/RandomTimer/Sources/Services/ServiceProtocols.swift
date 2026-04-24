import Foundation

@MainActor
protocol TimerNotificationHandling {
    func requestNotificationPermission() async
    func scheduleAlarmNotification(at date: Date, soundType: SoundType) async
    func cancelPendingNotifications() async
    func playAlarmSound(type: SoundType, volume: Float)
    func stopAlarmSound()
    func silenceAlarm()
    func startVibration()
    func stopVibration()
    func playPreviewSound(type: SoundType, volume: Float)
    func updatePreviewVolume(_ volume: Float)
    func previewVolume(type: SoundType, volume: Float)
    func stopPreview()
    var didTapAlarmNotification: Bool { get }
    func clearNotificationTapFlag()
    func scheduleReengagementReminder()
    func cancelReengagementReminders()
}

protocol TimerStorage: Sendable {
    func saveConfig(_ config: TimerConfig) async
    func loadConfig() async -> TimerConfig?
    func saveTimerState(_ state: TimerState) async
    func loadTimerState() async -> TimerState?
    func clearTimerState() async

    nonisolated func loadConfigSync() -> TimerConfig?
    nonisolated func loadTimerStateSync() -> TimerState?
    nonisolated func clearTimerStateSync()
}

@MainActor
protocol TimerLiveActivityHandling {
    func start(state: TimerState) async
    func update(state: TimerState) async
    func end() async
    func endAll() async
}

@MainActor
protocol BackgroundVoiceKeepAliveHandling {
    var isActive: Bool { get }
    func start()
    func stop()
}
