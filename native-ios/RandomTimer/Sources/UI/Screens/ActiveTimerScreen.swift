import SwiftUI

/// Screen shown when a timer is actively counting down
struct ActiveTimerScreen: View {
    @EnvironmentObject var timerManager: TimerManager
    @Environment(\.verticalSizeClass) private var verticalSizeClass
    @State private var showResetFeedback: Bool = false
    @State private var resetFeedbackTask: Task<Void, Never>?

    private var state: TimerState? {
        timerManager.timerState
    }

    private var isComplete: Bool {
        state?.status == .complete || state?.status == .alarm
    }

    private var isPaused: Bool {
        state?.status == .paused
    }

    private var rangeText: String {
        guard let config = state?.config else { return "" }
        return formatRangeText(minSeconds: config.minSeconds, maxSeconds: config.maxSeconds)
    }

    private var isLandscape: Bool {
        verticalSizeClass == .compact
    }

    private func formatRangeText(minSeconds: Int, maxSeconds: Int) -> String {
        func formatTime(_ seconds: Int) -> String {
            if seconds >= 60 {
                let mins = seconds / 60
                let secs = seconds % 60
                return secs > 0 ? "\(mins)m \(secs)s" : "\(mins)m"
            } else {
                return "\(seconds)s"
            }
        }
        return "\(formatTime(minSeconds)) - \(formatTime(maxSeconds))"
    }

    static func loopBadgeText(enabled: Bool, repeatRounds: Int, roundCount: Int) -> String {
        guard enabled else { return "Loop Off" }
        guard repeatRounds > 0 else { return "Infinite Loop" }

        let clampedRound = Swift.max(1, Swift.min(roundCount, repeatRounds))
        return "Loop On · Round \(clampedRound)/\(repeatRounds)"
    }

    static func loopBadgeAccessibilityLabel(enabled: Bool, repeatRounds: Int, roundCount: Int) -> String {
        guard enabled else { return "Loop disabled" }
        guard repeatRounds > 0 else { return "Infinite loop enabled" }

        let clampedRound = Swift.max(1, Swift.min(roundCount, repeatRounds))
        return "Loop on, round \(clampedRound) of \(repeatRounds)"
    }

    static func voiceBadgeText(enabled: Bool) -> String {
        enabled ? "Voice On" : "Voice Off"
    }

    static func voiceBadgeAccessibilityLabel(enabled: Bool) -> String {
        enabled ? "Voice callouts enabled" : "Voice callouts disabled"
    }

    var body: some View {
        ZStack {
            Color.backgroundDark.ignoresSafeArea()

            if let state = state {
                Group {
                    if isLandscape {
                        HStack(spacing: 24) {
                            VStack(spacing: 16) {
                                topControlBadges
                                .frame(height: 36)

                                statusText(for: state)
                                    .frame(height: 28)

                                CircularTimerView(
                                    progress: isComplete ? 1.0 : (state.unpredictableProgress),
                                    status: state.status,
                                    rangeText: rangeText
                                )
                                .accessibilityIdentifier("activeTimerCircle")
                                .onTapGesture {
                                    if state.status == .alarm {
                                        timerManager.silenceAlarm()
                                    } else if state.status == .complete {
                                        Task {
                                            await timerManager.dismissAlarm()
                                        }
                                    }
                                }
                                .accessibilityElement(children: .ignore)
                                .accessibilityLabel(isComplete ? "Timer complete" : "Timer running, range \(rangeText)")
                                .accessibilityValue(isPaused ? "Paused" : (isComplete ? "Complete" : "Active"))

                                Group {
                                    if showResetFeedback {
                                        Text("Timer restarted")
                                            .font(.subheadline)
                                            .foregroundColor(.accentPrimary)
                                    } else if isComplete {
                                        Text("Went off after \(state.targetDuration.formattedDuration)")
                                            .font(.subheadline)
                                            .foregroundColor(.textSecondary)
                                    } else {
                                        Text("You don't know when it will go off...")
                                            .font(.subheadline)
                                            .foregroundColor(isPaused ? .textSecondary : .textMuted)
                                    }
                                }
                                .frame(height: 20)

                                Group {
                                    if state.status == .alarm {
                                        loopBadge
                                    } else {
                                        Color.clear
                                    }
                                }
                                .frame(height: 36)
                            }
                            .frame(maxWidth: .infinity)

                            VStack {
                                Spacer()
                                actionButtons(for: state)
                                    .padding(.bottom, 8)
                            }
                            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom)
                        }
                        .padding(.horizontal, 24)
                        .padding(.vertical, 24)
                    } else {
                        VStack(spacing: 32) {
                            // Loop badge at top - use fixed height placeholder to prevent layout shift
                            topControlBadges
                            .frame(height: 36)

                            // Status text - fixed height to prevent layout shift
                            statusText(for: state)
                                .frame(height: 28)

                            // Circular Timer - ALWAYS show range (random timer - user should NEVER see countdown)
                            CircularTimerView(
                                progress: isComplete ? 1.0 : (state.unpredictableProgress),
                                status: state.status,
                                rangeText: rangeText
                            )
                            .accessibilityIdentifier("activeTimerCircle")
                            .onTapGesture {
                                if state.status == .alarm {
                                    timerManager.silenceAlarm()
                                } else if state.status == .complete {
                                    Task {
                                        await timerManager.dismissAlarm()
                                    }
                                }
                            }
                            .accessibilityElement(children: .ignore)
                            .accessibilityLabel(isComplete ? "Timer complete" : "Timer running, range \(rangeText)")
                            .accessibilityValue(isPaused ? "Paused" : (isComplete ? "Complete" : "Active"))

                            // Info message - fixed height placeholder to prevent layout shift
                            Group {
                                if showResetFeedback {
                                    Text("Timer restarted")
                                        .font(.subheadline)
                                        .foregroundColor(.accentPrimary)
                                } else if isComplete {
                                    Text("Went off after \(state.targetDuration.formattedDuration)")
                                        .font(.subheadline)
                                        .foregroundColor(.textSecondary)
                                } else {
                                    Text("You don't know when it will go off...")
                                        .font(.subheadline)
                                        .foregroundColor(isPaused ? .textSecondary : .textMuted)
                                }
                            }
                            .frame(height: 20)

                            // Alarm state: show loop toggle (fixed position)
                            Group {
                                if state.status == .alarm {
                                    loopBadge
                                } else {
                                    Color.clear
                                }
                            }
                            .frame(height: 36)

                            Spacer()

                            // Action buttons
                            actionButtons(for: state)
                                .padding(.horizontal, 24)
                                .padding(.bottom, 32)
                        }
                        .padding(.top, 48)
                    }
                }
            }
        }
        .navigationBarBackButtonHidden(true)
        .onAppear {
            AnalyticsService.shared.screen(AnalyticsScreens.activeTimer)
        }
        .onDisappear {
            resetFeedbackTask?.cancel()
            resetFeedbackTask = nil
            showResetFeedback = false
        }
    }

    private var loopBadge: some View {
        let isEnabled = timerManager.config.repeatEnabled
        let repeatRounds = state?.config.repeatRounds ?? timerManager.config.repeatRounds
        let roundCount = state?.roundCount ?? 1
        return controlBadge(
            text: Self.loopBadgeText(
                enabled: isEnabled,
                repeatRounds: repeatRounds,
                roundCount: roundCount
            ),
            systemImage: "repeat",
            enabled: isEnabled,
            accessibilityLabel: Self.loopBadgeAccessibilityLabel(
                enabled: isEnabled,
                repeatRounds: repeatRounds,
                roundCount: roundCount
            ),
            accessibilityHint: "Double-tap to toggle repeat timer"
        ) {
            updateConfig(repeatEnabled: !isEnabled)
        }
    }

    private var voiceBadge: some View {
        let isEnabled = state?.config.voiceEnabled ?? timerManager.config.voiceEnabled
        return controlBadge(
            text: Self.voiceBadgeText(enabled: isEnabled),
            systemImage: "waveform",
            enabled: isEnabled,
            accessibilityLabel: Self.voiceBadgeAccessibilityLabel(enabled: isEnabled),
            accessibilityHint: "Double-tap to toggle voice callouts"
        )
        {
            updateConfig(voiceEnabled: !isEnabled)
        }
    }

    private func controlBadge(
        text: String,
        systemImage: String,
        enabled: Bool,
        accessibilityLabel: String,
        accessibilityHint: String,
        action: @escaping () -> Void
    ) -> some View {
        return Button {
            action()
        } label: {
            Label(text, systemImage: systemImage)
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(enabled ? .accentPrimary : .textMuted)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(Color.glassBackground)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(enabled ? .accentPrimary : Color.glassBorder, lineWidth: 1)
                )
        }
        .accessibilityLabel(accessibilityLabel)
        .accessibilityHint(accessibilityHint)
    }

    @ViewBuilder
    private var topControlBadges: some View {
        if isComplete {
            Color.clear.frame(height: 36)
        } else {
            HStack(spacing: 12) {
                loopBadge
                voiceBadge
            }
        }
    }

    private func updateConfig(
        repeatEnabled: Bool? = nil,
        voiceEnabled: Bool? = nil
    ) {
        let current = timerManager.config
        let newConfig = TimerConfig(
            minSeconds: current.minSeconds,
            maxSeconds: current.maxSeconds,
            alarmDuration: current.alarmDuration,
            hiddenMode: current.hiddenMode,
            repeatEnabled: repeatEnabled ?? current.repeatEnabled,
            soundType: current.soundType,
            volume: current.volume,
            vibrationEnabled: current.vibrationEnabled,
            useExtendedRange: current.useExtendedRange,
            voiceEnabled: voiceEnabled ?? current.voiceEnabled,
            repeatRounds: current.repeatRounds
        )
        timerManager.updateConfig(newConfig)
    }

    @ViewBuilder
    private func statusText(for state: TimerState) -> some View {
        // Completion text is now shown inside the CircularTimerView
        // Only show status text for running/paused states
        Group {
            if state.status == .alarm || state.status == .complete {
                // Empty - completion message is inside the circle
                EmptyView()
            } else if isPaused {
                Text("Paused")
                    .font(.title3)
                    .foregroundColor(.textSecondary)
                    .transition(.opacity)
            } else {
                Text(statusMessage(for: state.status))
                    .font(.title3)
                    .foregroundColor(.textSecondary)
                    .transition(.opacity)
            }
        }
        .animation(.easeInOut(duration: 0.5), value: state.status)
    }

    private func statusMessage(for status: TimerStatus) -> String {
        switch status {
        case .running, .warning, .danger:
            return "Timer running..."
        default:
            return ""
        }
    }

    @ViewBuilder
    private func actionButtons(for state: TimerState) -> some View {
        VStack(spacing: 12) {
            if isComplete {
                // Silence - only shown during active alarm when sound is still playing
                if state.status == .alarm && !timerManager.isAlarmSilenced {
                    SecondaryButton(title: "Silence") {
                        timerManager.silenceAlarm()
                    }
                }

                // Stop - stops alarm and goes home
                DangerButton(title: "Stop") {
                    Task {
                        await timerManager.dismissAlarm()
                    }
                }

                // Reset - restart with same duration
                SecondaryButton(title: "Reset") {
                    Task {
                        await timerManager.resetTimer()
                        await MainActor.run {
                            triggerResetFeedback()
                        }
                    }
                }
            } else {
                // Pause / Resume
                PrimaryButton(
                    title: isPaused ? "Resume" : "Pause",
                    action: {
                        if isPaused {
                            timerManager.resumeTimer()
                        } else {
                            timerManager.pauseTimer()
                        }
                    }
                )

                // Reset (restart with same duration)
                SecondaryButton(title: "Reset") {
                    Task {
                        await timerManager.resetTimer()
                        await MainActor.run {
                            triggerResetFeedback()
                        }
                    }
                }

                // Stop (go back to home screen)
                SecondaryButton(title: "Stop") {
                    Task {
                        await timerManager.cancelTimer()
                    }
                }
            }
        }
    }

    private func triggerResetFeedback() {
        resetFeedbackTask?.cancel()
        showResetFeedback = true
        resetFeedbackTask = Task { @MainActor in
            try? await Task.sleep(for: .seconds(1.2))
            showResetFeedback = false
        }
    }
}

#Preview("Running") {
    ActiveTimerScreen()
        .environmentObject(TimerManager())
}
