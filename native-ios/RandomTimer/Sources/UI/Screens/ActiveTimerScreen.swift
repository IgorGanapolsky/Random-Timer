import SwiftUI

/// Screen shown when a timer is actively counting down
struct ActiveTimerScreen: View {
    @EnvironmentObject var timerManager: TimerManager
    @State private var loopEnabled: Bool = false // Default to LOOP OFF
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

    var body: some View {
        ZStack {
            Color.backgroundDark.ignoresSafeArea()

            if let state = state {
                VStack(spacing: 32) {
                    // Loop badge at top - use fixed height placeholder to prevent layout shift
                    Group {
                        if isComplete {
                            // Invisible placeholder with same height as badge
                            Color.clear.frame(height: 36)
                        } else {
                            loopBadge
                        }
                    }
                    .frame(height: 36)

                    // Status text - fixed height to prevent layout shift
                    statusText(for: state)
                        .frame(height: 28)

                    // Circular Timer - ALWAYS show range (random timer - user should NEVER see countdown)
                    // Hide progress ring since we're not revealing time info
                    CircularTimerView(
                        progress: isComplete ? 1.0 : 0, // Full progress ring when complete
                        status: state.status,
                        rangeText: rangeText // ALWAYS show range, never countdown
                    )
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
                                .foregroundColor(.textMuted)
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
        .navigationBarBackButtonHidden(true)
        .onAppear {
            // Initialize loop state from config (only on first appear)
            if let state = state {
                loopEnabled = state.config.repeatEnabled
            }
        }
        .onChange(of: state?.config.repeatEnabled) { _, newValue in
            // Sync local state when config changes externally
            if let newValue = newValue {
                loopEnabled = newValue
            }
        }
        .onDisappear {
            resetFeedbackTask?.cancel()
            resetFeedbackTask = nil
            showResetFeedback = false
        }
    }

    private var loopBadge: some View {
        Button {
            loopEnabled.toggle()
            updateLoopConfig()
        } label: {
            Label(loopEnabled ? "LOOP" : "LOOP OFF", systemImage: "repeat")
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(loopEnabled ? .accentPrimary : .textMuted)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(Color.glassBackground)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(loopEnabled ? Color.accentPrimary : Color.glassBorder, lineWidth: 1)
                )
        }
        .accessibilityLabel(loopEnabled ? "Loop enabled" : "Loop disabled")
        .accessibilityHint("Double-tap to toggle repeat timer")
    }

    private func updateLoopConfig() {
        var config = timerManager.config
        config = TimerConfig(
            minSeconds: config.minSeconds,
            maxSeconds: config.maxSeconds,
            alarmDuration: config.alarmDuration,
            hiddenMode: config.hiddenMode,
            repeatEnabled: loopEnabled,
            soundType: config.soundType,
            volume: config.volume
        )
        timerManager.updateConfig(config)
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
                    .foregroundColor(.textMuted)
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
                    },
                    backgroundColor: isPaused ? .timerActive : .accentPrimary
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
