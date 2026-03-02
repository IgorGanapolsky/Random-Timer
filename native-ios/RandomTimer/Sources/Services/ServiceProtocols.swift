import Foundation

// MARK: - Enums

public enum PaywallEntryPoint: String, Sendable {
    case soundGate = "sound_gate"
    case rangeGate = "range_gate"
    case settings = "settings"
    case unknown = "unknown"
}

public enum ProPurchaseResult: String, Sendable {
    case success, userCancelled, pending, productUnavailable, failed
}

public enum ProRestoreResult: String, Sendable {
    case restored, alreadyUnlocked, notFound
}

// MARK: - Protocols

@MainActor
protocol TimerNotificationHandling {
    func scheduleAlarmNotification(at date: Date, soundType: SoundType) async
    func cancelPendingNotifications() async
    func playAlarmSound(type: SoundType, volume: Float)
    func stopAlarmSound()
    func silenceAlarm()
    func startVibration()
    func stopVibration()
    func playPreviewSound(type: SoundType, volume: Float)
    func stopPreview()
    func updatePreviewVolume(_ volume: Float)
    func previewVolume(type: SoundType, volume: Float)
    func scheduleReengagementReminder()
    func cancelReengagementReminders()
    var didTapAlarmNotification: Bool { get }
    func clearNotificationTapFlag()
}

protocol TimerStorage: Sendable {
    func saveTimerConfig(_ config: TimerConfig) async
    func getTimerConfig() async -> TimerConfig
    func saveTimerState(_ state: TimerState) async
    func loadTimerState() async -> TimerState?
    func clearTimerState() async
    
    // Legacy support for TimerManager
    func saveConfig(_ config: TimerConfig) async
    func loadConfig() async -> TimerConfig?
    
    @MainActor func loadConfigSync() -> TimerConfig?
    @MainActor func loadTimerStateSync() -> TimerState?
    @MainActor func clearTimerStateSync()
}

@MainActor
protocol TimerLiveActivityHandling {
    func start(state: TimerState) async
    func update(state: TimerState)
    func end()
    func endAll() async
}

@MainActor
protocol AnalyticsHandling {
    func event(_ name: String, properties: [String: Any]?)
    func screen(_ name: String)
    func identify(userId: String, properties: [String: Any]?)
}
