import SwiftUI

/// Screen shown when a timer is actively counting down
struct ActiveTimerScreen: View {
    @EnvironmentObject var timerManager: TimerManager
    @Environment(\.verticalSizeClass) private var verticalSizeClass
    
    @State private var loopEnabled: Bool = false
    @State private var showResetFeedback: Bool = false
    @State private var resetFeedbackTask: Task<Void, Never>?

    private var state: TimerState? {
        timerManager.timerState
    }

    private var isComplete: Bool {
        state?.status == .alarm || state?.status == .complete
    }

    private var isPaused: Bool {
        state?.status == .paused
    }

    private var isLandscape: Bool {
        verticalSizeClass == .compact
    }

    private var rangeText: String {
        guard let config = state?.config else { return "" }
        return formatTimeRange(min: config.minSeconds, max: config.maxSeconds)
    }

    var body: some View {
        ZStack {
            Color.backgroundDark.ignoresSafeArea()

            if let state = state {
                Group {
                    if isLandscape {
                        HStack(spacing: 32) {
                            VStack(spacing: 16) {
                                // Loop badge at top - fixed height placeholder
                                Group {
                                    if !isComplete {
                                        loopBadge
                                    } else {
                                        Color.clear
                                    }
                                }
                                .frame(height: 36)

                                // Status text - fixed height placeholder
                                statusText(for: state)
                                    .frame(height: 28)

                                CircularTimerView(
                                    progress: isComplete ? 1.0 : (state.unpredictableProgress),
                                    status: state.status,
                                    rangeText: rangeText,
                                    isLandscape: true
                                )
                                .accessibilityIdentifier("activeTimerCircle")
                                .onTapGesture {
                                    guard isComplete else { return }
                                    Task {
                                        await timerManager.dismissAlarm()
                                    }
                                }

                                // Info message - fixed height placeholder
                                Group {
                                    if showResetFeedback {
                                        Text("Timer restarted")
                                            .font(.body)
                                            .foregroundColor(.accentPrimary)
                                    } else if isComplete {
                                        Text("Went off after \(TimeInterval(state.targetDuration).formattedDuration)")
                                            .font(.body)
                                            .foregroundColor(.textSecondary)
                                    } else {
                                        Color.clear
                                    }
                                }
                                .frame(height: 36)
                            }
                            .frame(maxWidth: .infinity)

                            ScrollView(showsIndicators: false) {
                                actionButtons(for: state)
                                    .padding(.vertical, 8)
                            }
                            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom)
                        }
                        .padding(.horizontal, 24)
                        .padding(.vertical, 24)
                    } else {
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
                            CircularTimerView(
                                progress: isComplete ? 1.0 : (state.unpredictableProgress),
                                status: state.status,
                                rangeText: rangeText,
                                isLandscape: false
                            )
                            .accessibilityIdentifier("activeTimerCircle")
                            .onTapGesture {
                                guard isComplete else { return }
                                Task {
                                    await timerManager.dismissAlarm()
                                }
                            }
                            .accessibilityElement(children: .ignore)
                            .accessibilityLabel(isComplete ? "Timer complete" : "Timer running, range \(rangeText)")
                            .accessibilityValue(isPaused ? "Paused" : (isComplete ? "Complete" : "Active"))

                            // Info message - fixed height placeholder to prevent layout shift
                            Group {
                                if showResetFeedback {
                                    Text("Timer restarted")
                                        .font(.body)
                                        .foregroundColor(.accentPrimary)
                                } else if isComplete {
                                    Text("Went off after \(TimeInterval(state.targetDuration).formattedDuration)")
                                        .font(.body)
                                        .foregroundColor(.textSecondary)
                                } else {
                                    Text("You don't know when it will go off...")
                                        .font(.body)
                                        .foregroundColor(isPaused ? .textSecondary : .textMuted)
                                }
                            }
                            .frame(height: 36)

                            // Alarm loop toggle (only shown during alarm)
                            if state.status == .alarm {
                                loopBadge
                            }

                            Spacer()

                            // Action buttons
                            actionButtons(for: state)
                                .padding(.horizontal, 24)
                                .padding(.bottom, 32)
                        }
                    }
                }
            }
        }
        .accessibilityIdentifier("activeTimerScreen")
        .onAppear {
            AnalyticsService.shared.screen(AnalyticsScreens.activeTimer)
            // Initialize loop state from config (only on first appear)
            if let state = state {
                loopEnabled = state.config.repeatEnabled
            }
        }
        .onDisappear {
            guard timerManager.timerState != nil else { return }
            let shouldDismissAlarm = isComplete
            Task {
                if shouldDismissAlarm {
                    await timerManager.dismissAlarm()
                } else {
                    await timerManager.cancelTimer()
                }
            }
        }
        .onChange(of: state?.config.repeatEnabled) { _, newValue in
            // Sync local state when config changes externally
            if let newValue = newValue {
                loopEnabled = newValue
            }
        }
    }

    // MARK: - Components

    private var loopBadge: some View {
        Button(action: {
            loopEnabled.toggle()
            updateConfigLoop()
        }) {
            HStack(spacing: 6) {
                Text("🔁")
                    .font(.body)
                Text(loopEnabled ? "LOOP" : "LOOP OFF")
                    .font(.caption)
                    .fontWeight(.medium)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.glassBackground)
            .foregroundColor(loopEnabled ? .accentPrimary : .textMuted)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(loopEnabled ? Color.accentPrimary : Color.glassBorder, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }

    private func updateConfigLoop() {
        guard let config = state?.config else { return }
        let newConfig = TimerConfig(
            minSeconds: config.minSeconds,
            maxSeconds: config.maxSeconds,
            alarmDuration: config.alarmDuration,
            hiddenMode: config.hiddenMode,
            repeatEnabled: loopEnabled,
            soundType: config.soundType,
            volume: config.volume
        )
        timerManager.updateConfig(newConfig)
    }

    @ViewBuilder
    private func statusText(for state: TimerState) -> some View {
        ZStack {
            if isPaused {
                Text("Paused")
                    .font(.title3)
                    .foregroundColor(.textSecondary)
                    .accessibilityIdentifier("statusLabel")
                    .transition(.opacity)
            } else {
                Text(statusMessage(for: state.status))
                    .font(.title3)
                    .foregroundColor(.textSecondary)
                    .accessibilityIdentifier("statusLabel")
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
                PrimaryButton(title: isPaused ? "Resume" : "Pause") {
                    if isPaused {
                        timerManager.resumeTimer()
                    } else {
                        timerManager.pauseTimer()
                    }
                }

                HStack(spacing: 12) {
                    // Reset
                    SecondaryButton(title: "Reset") {
                        Task {
                            await timerManager.resetTimer()
                            await MainActor.run {
                                triggerResetFeedback()
                            }
                        }
                    }

                    // Stop
                    SecondaryButton(title: "Stop") {
                        Task {
                            await timerManager.cancelTimer()
                        }
                    }
                }
            }
        }
    }

    private func formatTimeRange(min: Int, max: Int) -> String {
        func format(seconds: Int) -> String {
            if seconds >= 60 {
                let mins = seconds / 60
                let secs = seconds % 60
                return secs > 0 ? "\(mins)m \(secs)s" : "\(mins)m"
            }
            return "\(seconds)s"
        }
        return "\(format(seconds: min)) - \(format(seconds: max))"
    }

    private func triggerResetFeedback() {
        resetFeedbackTask?.cancel()
        showResetFeedback = true
        resetFeedbackTask = Task { @MainActor in
            try? await Task.sleep(for: .seconds(2.0))
            showResetFeedback = false
        }
    }
}

#Preview("Running") {
    ActiveTimerScreen()
        .environmentObject(TimerManager())
}
