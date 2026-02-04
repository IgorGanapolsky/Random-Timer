import Foundation
import Combine
import ActivityKit
import UserNotifications

/// Main timer management class using Swift 6 concurrency
@MainActor
final class TimerManager: ObservableObject {

    // MARK: - Published State

    /// Load config synchronously at property initialization to avoid UI flicker
    @Published private(set) var config: TimerConfig = TimerManager.loadInitialConfig()
    @Published private(set) var timerState: TimerState?

    // MARK: - Private Properties

    private var timerTask: Task<Void, Never>?
    private var activity: Activity<TimerActivityAttributes>?
    private let storageService = StorageService()
    private let notificationService = NotificationService()

    /// Load config directly from UserDefaults before any SwiftUI rendering
    private nonisolated static func loadInitialConfig() -> TimerConfig {
        guard let data = UserDefaults.standard.data(forKey: "timer_config"),
              let config = try? JSONDecoder().decode(TimerConfig.self, from: data) else {
            return .default
        }
        return config
    }

    // MARK: - Initialization

    init() {
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

    /// End all Live Activities (used on app start to clean up stale activities)
    private func endAllLiveActivities() async {
        for activity in Activity<TimerActivityAttributes>.activities {
            await activity.end(nil, dismissalPolicy: .immediate)
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

        // Schedule notification
        await notificationService.scheduleAlarmNotification(at: state.endDate)

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

    func resetTimer() async {
        // Reset to the SAME duration (restart from beginning)
        guard let currentState = timerState else { return }
        let sameDuration = currentState.targetDuration

        notificationService.stopAlarmSound()
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

        // Schedule notification
        await notificationService.scheduleAlarmNotification(at: newState.endDate)

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

    // MARK: - Live Activity

    private func startLiveActivity(state: TimerState) async {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        let attributes = TimerActivityAttributes(
            endDate: state.endDate,
            minSeconds: state.config.minSeconds,
            maxSeconds: state.config.maxSeconds
        )
        let contentState = TimerActivityAttributes.ContentState(
            status: state.status,
            remainingSeconds: Int(state.remainingDuration)
        )

        // Set staleDate 5 seconds in future - if app stops updating, iOS will mark as stale
        let staleDate = Date().addingTimeInterval(5)

        do {
            activity = try Activity.request(
                attributes: attributes,
                content: .init(state: contentState, staleDate: staleDate),
                pushType: nil
            )
        } catch {
            print("Failed to start Live Activity: \(error)")
        }
    }

    @MainActor
    private func updateLiveActivity(state: TimerState) {
        let contentState = TimerActivityAttributes.ContentState(
            status: state.status,
            remainingSeconds: Int(state.remainingDuration)
        )

        // Set staleDate 5 seconds in future - keeps refreshing as long as app updates
        let staleDate = Date().addingTimeInterval(5)

        guard let currentActivity = activity else { return }
        Task {
            await currentActivity.update(
                ActivityContent(state: contentState, staleDate: staleDate)
            )
        }
    }

    @MainActor
    private func endLiveActivity() {
        guard let currentActivity = activity else { return }
        Task {
            await currentActivity.end(nil, dismissalPolicy: .immediate)
        }
        activity = nil
    }
}
