import Foundation
import Combine

/// Main timer management class using Swift 6 concurrency
@MainActor
final class TimerManager: ObservableObject {

    // MARK: - Published State

    /// Load config synchronously at property initialization to avoid UI flicker
    @Published private(set) var config: TimerConfig = TimerManager.loadInitialConfig()
    @Published private(set) var timerState: TimerState?

    // MARK: - Private Properties

    private var timerTask: Task<Void, Never>?
    nonisolated private let storageService: TimerStorage
    private let notificationService: TimerNotificationHandling
    private let liveActivityService: TimerLiveActivityHandling

    /// Load config directly from UserDefaults before any SwiftUI rendering
    private nonisolated static func loadInitialConfig() -> TimerConfig {
        guard let data = UserDefaults.standard.data(forKey: "timer_config"),
              let config = try? JSONDecoder().decode(TimerConfig.self, from: data) else {
            return .default
        }
        return config
    }

    // MARK: - Initialization

    init(
        storageService: TimerStorage = StorageService(),
        notificationService: TimerNotificationHandling = NotificationService(),
        liveActivityService: TimerLiveActivityHandling = LiveActivityService()
    ) {
        self.storageService = storageService
        self.notificationService = notificationService
        self.liveActivityService = liveActivityService

        // Wire Bluetooth/CarPlay media button to dismiss alarm
        if let notificationService = notificationService as? NotificationService {
            notificationService.onMediaButtonDismiss = { [weak self] in
                Task { @MainActor in
                    await self?.dismissAlarm()
                }
            }
        }

        // Stop any alarm/vibration that might still be playing from a previous session
        notificationService.stopAlarmSound()
        notificationService.stopVibration()

        // Check synchronously if there's a stale alarm/complete state and clear it
        // This prevents showing the alarm screen when reopening after force close
        if let savedState = storageService.loadTimerStateSync() {
            if savedState.status == .alarm || savedState.status == .complete {
                storageService.clearTimerStateSync()
                // timerState stays nil - go to home screen
            } else {
                // There's an active timer - restore it async
                Task {
                    await endAllLiveActivities()
                    await restoreActiveTimer()
                }
            }
        }

        Task {
            // End any stale Live Activities from previous sessions
            await endAllLiveActivities()
        }
    }

    // MARK: - Public Methods

    func updateConfig(_ newConfig: TimerConfig) {
        config = newConfig
        Task {
            await storageService.saveConfig(newConfig)
        }
    }

    func startTimer() async {
        // Stop any preview sound
        notificationService.stopPreview()

        // Generate random duration
        let randomDuration = generateRandomDuration(
            min: config.minDuration,
            max: config.maxDuration
        )

        let state = TimerState(
            config: config,
            targetDuration: randomDuration
        )

        timerState = state

        // Save state for recovery
        await storageService.saveTimerState(state)

        // Start Live Activity
        await startLiveActivity(state: state)

        // Schedule notification with the configured alarm sound
        await notificationService.scheduleAlarmNotification(at: state.endDate, soundType: config.soundType)

        // Start countdown
        startCountdown()
    }

    func cancelTimer() async {
        stopCountdown()
        timerState = nil

        await storageService.clearTimerState()
        endLiveActivity()
        await notificationService.cancelPendingNotifications()
    }

    func dismissAlarm() async {
        notificationService.stopAlarmSound()
        notificationService.stopVibration()
        await cancelTimer()
    }

    func pauseTimer() {
        guard var state = timerState, state.status != .paused else { return }
        stopCountdown()
        state.status = .paused
        timerState = state
    }

    func resumeTimer() {
        guard var state = timerState, state.status == .paused else { return }
        state.status = TimerStatus.from(
            remainingSeconds: state.remainingDuration,
            currentStatus: .running
        )
        timerState = state
        startCountdown()
    }

    func restartTimer() async {
        // Restart with a NEW random duration (used after alarm completes with loop)
        notificationService.stopAlarmSound()
        await cancelTimer()
        await startTimer()
    }

    /// Call synchronously when app enters background to prevent AVAudioPlayer auto-resume
    func handleBackground() {
        guard let state = timerState, state.status == .alarm else { return }
        // Deactivate audio session so iOS won't auto-resume playback on foreground
        notificationService.stopAlarmSound()
        notificationService.stopVibration()
    }

    func handleForeground() async {
        // Handle returning to foreground while alarm is active
        if var state = timerState, state.status == .alarm {
            if let alarmStart = state.alarmStartedAt {
                let elapsed = Date().timeIntervalSince(alarmStart)
                let alarmDuration = TimeInterval(state.config.alarmDuration)
                if elapsed >= alarmDuration {
                    // Alarm should have finished while we were backgrounded
                    stopCountdown()
                    notificationService.stopAlarmSound()
                    notificationService.stopVibration()
                    await notificationService.cancelPendingNotifications()

                    if state.config.repeatEnabled {
                        await restartTimer()
                    } else {
                        state.status = .complete
                        state.alarmTimeRemaining = 0
                        timerState = state
                    }
                    return
                } else {
                    // Alarm is still valid — update remaining time from wall clock
                    let remaining = alarmDuration - elapsed
                    state.alarmTimeRemaining = remaining
                    timerState = state
                    return
                }
            }
            return
        }

        guard var state = timerState,
              state.status != .alarm && state.status != .complete && state.status != .paused else { return }

        // Recalculate remaining time from the real clock
        let elapsed = Date().timeIntervalSince(state.startedAt)
        let remaining = state.targetDuration - elapsed

        if remaining <= 0 {
            // Timer expired while backgrounded
            // The alarm would have started at endDate (wall clock)
            let alarmStartDate = state.endDate
            let alarmDuration = TimeInterval(state.config.alarmDuration)
            let alarmElapsed = Date().timeIntervalSince(alarmStartDate)

            if alarmElapsed >= alarmDuration {
                // Alarm duration already passed while backgrounded — go straight to complete
                stopCountdown()
                notificationService.stopAlarmSound()
                notificationService.stopVibration()
                await notificationService.cancelPendingNotifications()
                notificationService.clearNotificationTapFlag()
                    endLiveActivity()

                if state.config.repeatEnabled {
                    await restartTimer()
                } else {
                    state.remainingDuration = 0
                    state.status = .complete
                    state.alarmTimeRemaining = 0
                    state.alarmStartedAt = alarmStartDate
                    timerState = state
                }
                return
            }

            // Alarm is still within its duration — show alarm with correct remaining time
            state.remainingDuration = 0
            state.status = .alarm
            state.alarmStartedAt = alarmStartDate
            state.alarmTimeRemaining = alarmDuration - alarmElapsed
            timerState = state
            await storageService.saveTimerState(state)

            stopCountdown()

            if notificationService.didTapAlarmNotification {
                // User tapped the notification to get here — don't replay alarm sound,
                // just stop the notification sound and show the alarm screen
                notificationService.stopAlarmSound()
                notificationService.stopVibration()
                await notificationService.cancelPendingNotifications()
                notificationService.clearNotificationTapFlag()
            } else {
                // App came to foreground some other way (e.g. task switcher) — play alarm
                notificationService.playAlarmSound(type: state.config.soundType, volume: state.config.volume)
                if state.config.vibrationEnabled {
                    notificationService.startVibration()
                }
            }
            endLiveActivity()
            startAlarmCountdown()
        } else {
            // Update remaining time and restart countdown
            state.remainingDuration = remaining
            state.status = TimerStatus.from(remainingSeconds: remaining, currentStatus: .running)
            timerState = state
            startCountdown()
        }
    }

    func resetTimer() async {
        // Reset to the SAME duration (restart from beginning)
        guard let currentState = timerState else { return }
        let sameDuration = currentState.targetDuration

        // If an alarm is currently active, stop sound/vibration before restarting
        notificationService.stopAlarmSound()
        notificationService.stopVibration()
        notificationService.clearNotificationTapFlag()
        stopCountdown()
        endLiveActivity()
        await notificationService.cancelPendingNotifications()

        // Create new state with same duration
        let newState = TimerState(
            config: currentState.config,
            targetDuration: sameDuration
        )

        timerState = newState

        // Save state for recovery
        await storageService.saveTimerState(newState)

        // Start Live Activity
        await startLiveActivity(state: newState)

        // Schedule notification with the configured alarm sound
        await notificationService.scheduleAlarmNotification(at: newState.endDate, soundType: currentState.config.soundType)

        // Start countdown
        startCountdown()
    }

    func previewSound() {
        notificationService.playPreviewSound(
            type: config.soundType,
            volume: config.volume
        )
    }

    func updatePreviewVolume() {
        notificationService.updatePreviewVolume(config.volume)
    }

    func previewVolume() {
        notificationService.previewVolume(
            type: config.soundType,
            volume: config.volume
        )
    }

    /// Test-only hook for setting timer state without waiting on async countdowns.
    func _setTimerStateForTesting(_ state: TimerState?) {
        timerState = state
    }

    // MARK: - Private Methods

    private func generateRandomDuration(min: TimeInterval, max: TimeInterval) -> TimeInterval {
        guard min < max else { return min }
        return TimeInterval.random(in: min...max)
    }

    private func loadSavedConfig() async {
        if let saved = await storageService.loadConfig() {
            config = saved
        }
    }

    private func restoreActiveTimer() async {
        guard let saved = await storageService.loadTimerState() else { return }

        // If the saved state was already in alarm or complete, clear it and go to home
        // This prevents alarm from replaying when force-closing during alarm and reopening
        if saved.status == .alarm || saved.status == .complete {
            await storageService.clearTimerState()
            timerState = nil
            return
        }

        // Calculate remaining time
        let elapsed = Date().timeIntervalSince(saved.startedAt)
        let remaining = saved.targetDuration - elapsed

        if remaining > 0 {
            var restored = saved
            restored.remainingDuration = remaining
            restored.status = TimerStatus.from(remainingSeconds: remaining, currentStatus: .running)
            timerState = restored

            await startLiveActivity(state: restored)
            startCountdown()
        } else {
            // Timer should have completed while app was closed - go to complete state, don't replay alarm
            await storageService.clearTimerState()
            timerState = nil
        }
    }

    private func startCountdown() {
        timerTask?.cancel()

        timerTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(1))

                guard !Task.isCancelled else { break }

                await self?.tick()
            }
        }
    }

    private func stopCountdown() {
        timerTask?.cancel()
        timerTask = nil
    }

    private func tick() async {
        guard var state = timerState else {
            print("[TimerManager] tick: no timerState")
            return
        }

        state.remainingDuration -= 1
        print("[TimerManager] tick: remaining = \(state.remainingDuration)")

        if state.remainingDuration <= 0 {
            state.remainingDuration = 0
            state.status = .alarm
            state.alarmTimeRemaining = TimeInterval(state.config.alarmDuration)
            state.alarmStartedAt = Date()
            timerState = state

            // Save alarm state so we can detect it on app restart
            await storageService.saveTimerState(state)

            stopCountdown()

            print("[TimerManager] ALARM! Playing sound type: \(state.config.soundType), volume: \(state.config.volume)")
            notificationService.playAlarmSound(
                type: state.config.soundType,
                volume: state.config.volume
            )
            if state.config.vibrationEnabled {
                print("[TimerManager] Starting vibration...")
                notificationService.startVibration()
            }
            // End Live Activity when alarm triggers - we don't need it anymore
            endLiveActivity()

            // Start alarm duration countdown
            startAlarmCountdown()

        } else {
            state.status = TimerStatus.from(
                remainingSeconds: state.remainingDuration,
                currentStatus: state.status
            )
            timerState = state

            await storageService.saveTimerState(state)
            updateLiveActivity(state: state)
        }
    }

    private func startAlarmCountdown() {
        timerTask?.cancel()

        timerTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(1))
                guard !Task.isCancelled else { break }

                await self?.alarmTick()
            }
        }
    }

    private func alarmTick() async {
        guard var state = timerState, state.status == .alarm else { return }

        state.alarmTimeRemaining -= 1

        if state.alarmTimeRemaining <= 0 {
            state.alarmTimeRemaining = 0
            state.status = .complete
            timerState = state

            stopCountdown()
            notificationService.stopAlarmSound()
            notificationService.stopVibration()

            // Auto-repeat if enabled
            if state.config.repeatEnabled {
                await restartTimer()
            }
        } else {
            timerState = state
        }
    }

    // MARK: - Live Activity Handling

    private func startLiveActivity(state: TimerState) async {
        await liveActivityService.start(state: state)
    }

    private func updateLiveActivity(state: TimerState) {
        liveActivityService.update(state: state)
    }

    private func endLiveActivity() {
        liveActivityService.end()
    }

    private func endAllLiveActivities() async {
        await liveActivityService.endAll()
    }
}
