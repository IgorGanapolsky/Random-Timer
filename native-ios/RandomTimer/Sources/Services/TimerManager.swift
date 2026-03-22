import Foundation
import Combine
import os

/// Main timer management class using Swift 6 concurrency
@MainActor
final class TimerManager: ObservableObject {

    // MARK: - Published State

    @Published private(set) var config: TimerConfig = .default
    @Published private(set) var timerState: TimerState?
    @Published private(set) var isAlarmSilenced: Bool = false

    // MARK: - Private Properties

    private var timerTask: Task<Void, Never>?
    nonisolated private let storageService: TimerStorage
    private let notificationService: TimerNotificationHandling
    private let liveActivityService: TimerLiveActivityHandling

    // MARK: - Initialization

    init(
        storageService: TimerStorage = StorageService(),
        notificationService: TimerNotificationHandling = NotificationService(),
        liveActivityService: TimerLiveActivityHandling = LiveActivityService()
    ) {
        self.storageService = storageService
        self.notificationService = notificationService
        self.liveActivityService = liveActivityService

        // Load config synchronously from storage to avoid UI flicker.
        // Clamp to current Pro entitlement so expired Pro users don't retain Pro-only values.
        let rawConfig = storageService.loadConfigSync() ?? .default
        self.config = rawConfig.clamped(isPro: ProManager.shared.isPro)

        // Wire Bluetooth/CarPlay media button and notification action callbacks.
        // Media button behavior must match timer-circle tap (silence + stay on timer screen).
        if let notificationService = notificationService as? NotificationService {
            notificationService.onMediaButtonSilence = { [weak self] in
                Task { @MainActor in
                    self?.silenceAlarm()
                }
            }
            notificationService.onNotificationStop = { [weak self] in
                Task { @MainActor in
                    await self?.dismissAlarm()
                }
            }
            notificationService.onNotificationSilence = { [weak self] in
                Task { @MainActor in
                    self?.silenceAlarm()
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

        // Sync config into running timer state so alarmTick sees the change
        if var state = timerState {
            state.config = newConfig
            timerState = state
        }

        AnalyticsService.shared.track(AnalyticsEvents.settingsChanged, properties: [
            "min_duration": newConfig.minDuration,
            "max_duration": newConfig.maxDuration,
            "sound_type": String(describing: newConfig.soundType),
            "repeat_enabled": newConfig.repeatEnabled,
            "voice_callouts_enabled": newConfig.voiceEnabled,
        ])

        Task {
            await storageService.saveConfig(newConfig)
        }
    }

    func startTimer(roundCount: Int = 1) async {
        // Reset silence flag for new timer
        isAlarmSilenced = false

        // Reset voice callout session for fresh chaos drill timing
        AIVoiceCalloutService.shared.resetSession()

        // Stop any preview sound
        notificationService.stopPreview()

        // Generate random duration
        let randomDuration = generateRandomDuration(
            min: config.minDuration,
            max: config.maxDuration
        )

        let state = TimerState(
            config: config,
            targetDuration: randomDuration,
            roundCount: roundCount
        )

        timerState = state

        AnalyticsService.shared.track(AnalyticsEvents.timerStarted, properties: [
            "min_duration": config.minDuration,
            "max_duration": config.maxDuration,
            "target_duration": randomDuration,
        ])
        AnalyticsService.shared.trackFirstTimerConfiguredIfNeeded()

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
        AnalyticsService.shared.track(AnalyticsEvents.timerStopped)
        if let state = timerState, state.status != .alarm, state.status != .complete {
            AnalyticsService.shared.track(AnalyticsEvents.timerAbandoned, properties: [
                "target_duration": state.targetDuration,
                "remaining_duration": state.remainingDuration,
                "status": state.status.rawValue,
                AnalyticsProperties.abandonReason: AnalyticsValues.abandonReasonUserCancelled,
                AnalyticsProperties.abandonSource: AnalyticsValues.abandonSourceTimerControls,
            ])
        }
        stopCountdown()
        timerState = nil

        await storageService.clearTimerState()
        await endLiveActivity()
        await notificationService.cancelPendingNotifications()
    }

    func dismissAlarm() async {
        AnalyticsService.shared.track(AnalyticsEvents.alarmDismissed)
        notificationService.stopAlarmSound()
        notificationService.stopVibration()
        // Schedule re-engagement reminders before clearing timer state
        notificationService.scheduleReengagementReminder()
        await cancelTimer()
    }

    /// Stops sound and vibration but keeps alarm state and countdown active
    func silenceAlarm() {
        notificationService.silenceAlarm()
        if timerState?.status == .alarm {
            isAlarmSilenced = true
        }
    }

    func pauseTimer() {
        guard var state = timerState, state.status != .paused else { return }
        AnalyticsService.shared.track(AnalyticsEvents.timerPaused)
        stopCountdown()
        state.status = .paused
        timerState = state
    }

    func resumeTimer() {
        guard var state = timerState, state.status == .paused else { return }
        AnalyticsService.shared.track(AnalyticsEvents.timerResumed)
        state.status = TimerStatus.from(
            remainingSeconds: state.remainingDuration,
            currentStatus: .running
        )
        timerState = state
        startCountdown()
    }

    func restartTimer() async {
        let currentRound = timerState?.roundCount ?? 1
        // Restart with a NEW random duration (used after alarm completes with loop)
        notificationService.stopAlarmSound()
        await cancelTimer()
        await startTimer(roundCount: currentRound + 1)
    }

    /// Call synchronously when app enters background to prevent AVAudioPlayer auto-resume.
    /// Treats backgrounding during alarm as a silence action (like Android's ScreenOffReceiver)
    /// so the alarm does NOT restart when returning to foreground.
    func handleBackground() {
        guard let state = timerState, state.status == .alarm else { return }
        // Silence alarm — stops sound/vibration AND marks as silenced so
        // handleForeground() won't restart the alarm when the user returns.
        silenceAlarm()
    }

    /// Check for pending actions from Live Activity intents (via shared App Group UserDefaults)
    func processPendingLiveActivityAction() async {
        let defaults = UserDefaults(suiteName: timerAppGroupSuite)
        guard let rawAction = defaults?.string(forKey: timerPendingActionKey),
              let action = TimerAction(rawValue: rawAction) else { return }

        // Clear the pending action immediately
        defaults?.removeObject(forKey: timerPendingActionKey)

        switch action {
        case .stop:
            if timerState?.status == .alarm {
                await dismissAlarm()
            } else {
                await cancelTimer()
            }
        case .pause:
            pauseTimer()
        case .resume:
            resumeTimer()
        }
    }

    func handleForeground() async {
        // User is back — cancel any pending re-engagement reminders
        notificationService.cancelReengagementReminders()

        // Process any pending actions from Live Activity buttons
        await processPendingLiveActivityAction()

        // Handle returning to foreground while alarm is already active
        // (alarm started in foreground, user backgrounded, then returned)
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
                    notificationService.clearNotificationTapFlag()
                    isAlarmSilenced = true

                    if state.config.repeatEnabled {
                        let shouldContinue = state.config.repeatRounds == 0 || state.roundCount < state.config.repeatRounds
                        if shouldContinue {
                            await restartTimer()
                        } else {
                            state.status = .complete
                            state.alarmTimeRemaining = 0
                            timerState = state
                        }
                    } else {
                        state.status = .complete
                        state.alarmTimeRemaining = 0
                        timerState = state
                    }
                    return
                } else {
                    // Alarm is still within its duration
                    let remaining = alarmDuration - elapsed
                    state.alarmTimeRemaining = remaining

                    if notificationService.didTapAlarmNotification {
                        // User tapped notification — silence everything
                        notificationService.stopAlarmSound()
                        notificationService.stopVibration()
                        notificationService.clearNotificationTapFlag()
                        isAlarmSilenced = true
                    } else if !isAlarmSilenced {
                        // Returning via task switcher — restart sound + vibration
                        // (handleBackground stopped them)
                        notificationService.playAlarmSound(
                            type: state.config.soundType,
                            volume: state.config.volume
                        )
                        if state.config.vibrationEnabled {
                            notificationService.startVibration()
                        }
                    }

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
                    await endLiveActivity()

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

            // Check notification tap BEFORE setting timerState so both
            // isAlarmSilenced and timerState update in the same UI frame
            let wasNotificationTap = notificationService.didTapAlarmNotification
            if wasNotificationTap {
                isAlarmSilenced = true
            }
            timerState = state

            stopCountdown()

            if wasNotificationTap {
                // User tapped the notification to get here — don't replay alarm sound
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
            await storageService.saveTimerState(state)
            await endLiveActivity()
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
        AnalyticsService.shared.track(AnalyticsEvents.timerReset)
        // Reset to the SAME duration (restart from beginning)
        guard let currentState = timerState else { return }
        let sameDuration = currentState.targetDuration

        AIVoiceCalloutService.shared.resetSession()

        // Reset silence flag for new timer
        isAlarmSilenced = false

        // If an alarm is currently active, stop sound/vibration before restarting
        notificationService.stopAlarmSound()
        notificationService.stopVibration()
        notificationService.clearNotificationTapFlag()
        stopCountdown()
        await endLiveActivity()
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

    func previewSound(type: SoundType) {
        notificationService.playPreviewSound(
            type: type,
            volume: config.volume
        )
    }

    func previewCommandCue() {
        AIVoiceCalloutService.shared.previewCommandCue()
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

    /// Test-only hook for simulating notification tap.
    func setNotificationTapFlagForTesting() {
        if let ns = notificationService as? NotificationService {
            ns.setDidTapAlarmNotificationForTesting(true)
        }
    }

    // MARK: - Private Methods

    private func generateRandomDuration(min: TimeInterval, max: TimeInterval) -> TimeInterval {
        guard min < max else { return min }
        return TimeInterval.random(in: min...max)
    }

    private func loadSavedConfig() async {
        if let saved = await storageService.loadConfig() {
            // Clamp to current Pro entitlement so expired Pro users don't retain Pro-only values.
            config = saved.clamped(isPro: ProManager.shared.isPro)
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
            AnalyticsService.shared.track(AnalyticsEvents.timerAbandoned, properties: [
                "target_duration": saved.targetDuration,
                "remaining_duration": 0,
                "status": saved.status.rawValue,
                AnalyticsProperties.abandonReason: AnalyticsValues.abandonReasonStaleRestoreExpired,
                AnalyticsProperties.abandonSource: AnalyticsValues.abandonSourceStateRestore,
            ])
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

                await self?.processPendingLiveActivityAction()
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
            Logger.timer.debug("tick: no timerState")
            return
        }

        state.remainingDuration -= 1
        Logger.timer.debug("tick: remaining = \(state.remainingDuration)")

        // Trigger voice callouts for Pro users
        if ProManager.shared.isPro {
            AIVoiceCalloutService.shared.triggerCallout(elapsedSeconds: Int(state.targetDuration - state.remainingDuration))
        }

        if state.remainingDuration <= 0 {
            state.remainingDuration = 0
            state.status = .alarm
            state.alarmTimeRemaining = TimeInterval(state.config.alarmDuration)
            state.alarmStartedAt = Date()
            timerState = state

            // Save alarm state so we can detect it on app restart
            await storageService.saveTimerState(state)

            stopCountdown()

            AnalyticsService.shared.track(AnalyticsEvents.timerCountdownFinished, properties: [
                "target_duration": state.targetDuration,
            ])
            AnalyticsService.shared.track(AnalyticsEvents.alarmTriggered, properties: [
                "target_duration": state.targetDuration,
            ])

            Logger.timer.info("ALARM! Playing sound type: \(String(describing: state.config.soundType)), volume: \(state.config.volume)")
            notificationService.playAlarmSound(
                type: state.config.soundType,
                volume: state.config.volume
            )
            if state.config.vibrationEnabled {
                Logger.timer.info("Starting vibration...")
                notificationService.startVibration()
            }
            // End Live Activity when alarm triggers - we don't need it anymore
            await endLiveActivity()

            // Start alarm duration countdown
            startAlarmCountdown()

        } else {
            state.status = TimerStatus.from(
                remainingSeconds: state.remainingDuration,
                currentStatus: state.status
            )
            timerState = state

            await storageService.saveTimerState(state)
            await updateLiveActivity(state: state)
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
            StoreReviewManager.shared.recordCompletion()
            TrainingStatsService.shared.recordSession()
            UserDefaults.standard.set(true, forKey: "hasCompletedFirstTimer")
            AnalyticsService.shared.track(AnalyticsEvents.timerCompleted, properties: [
                "target_duration": state.targetDuration,
                AnalyticsProperties.entitlementLevel: ProManager.shared.entitlementLevel.rawValue,
            ])
            AnalyticsService.shared.trackFirstTimerCompletedIfNeeded()

            // Schedule re-engagement reminders so user gets nudged back
            notificationService.scheduleReengagementReminder()

            // Auto-repeat if enabled
            if state.config.repeatEnabled {
                let shouldContinue = state.config.repeatRounds == 0 || state.roundCount < state.config.repeatRounds
                if shouldContinue {
                    await restartTimer()
                } else {
                    AnalyticsService.shared.track("loop_limit_reached", properties: [
                        "rounds": state.roundCount
                    ])
                }
            }
        } else {
            timerState = state
        }
    }

    // MARK: - Live Activity Handling

    private func startLiveActivity(state: TimerState) async {
        await liveActivityService.start(state: state)
    }

    private func updateLiveActivity(state: TimerState) async {
        await liveActivityService.update(state: state)
    }

    private func endLiveActivity() async {
        await liveActivityService.end()
    }

    private func endAllLiveActivities() async {
        await liveActivityService.endAll()
    }
}
