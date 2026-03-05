import SwiftUI

/// Screen shown when a timer is actively counting down
struct ActiveTimerScreen: View {
    @EnvironmentObject var timerManager: TimerManager
    @Environment(\.verticalSizeClass) private var verticalSizeClass
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

    var body: some View {
        ZStack {
            Color.backgroundDark.ignoresSafeArea()

            if let state = state {
                // Main content container - uses a stable vertical stack
                VStack(spacing: 0) {
                    if isLandscape {
                        landscapeLayout(state: state)
                    } else {
                        portraitLayout(state: state)
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                
                // Action buttons as a fixed-position overlay to prevent any layout shifts in the main circle
                VStack {
                    Spacer()
                    actionButtons(for: state)
                        .padding(.horizontal, 24)
                        .padding(.bottom, isLandscape ? 24 : 48)
                }
                .ignoresSafeArea(.keyboard)
            }
        }
        .navigationBarBackButtonHidden(true)
        .onAppear {
            AnalyticsService.shared.screen(AnalyticsScreens.activeTimer)
            if let state = state {
                loopEnabled = state.config.repeatEnabled
            }
        }
        .onChange(of: state?.config.repeatEnabled) { _, newValue in
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

    @ViewBuilder
    private func portraitLayout(state: TimerState) -> some View {
        VStack(spacing: 0) {
            Spacer().frame(height: 48)
            
            // Fixed height container for top elements
            ZStack {
                if !isComplete {
                    loopBadge
                }
            }
            .frame(height: 40)
            
            Spacer().frame(height: 24)
            
            // Status text - fixed height to prevent vertical jitter
            statusText(for: state)
                .frame(height: 32)
            
            Spacer().frame(height: 32)

            CircularTimerView(
                progress: isComplete ? 1.0 : state.unpredictableProgress,
                status: state.status,
                rangeText: rangeText
            )
            .accessibilityIdentifier("activeTimerCircle")
            .onTapGesture {
                guard state.status == .alarm else { return }
                timerManager.silenceAlarm()
            }

            Spacer().frame(height: 32)

            // Info message - fixed height
            ZStack {
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
            .frame(height: 24)

            Spacer().frame(height: 24)
            
            // Alarm state loop badge placeholder
            ZStack {
                if state.status == .alarm {
                    loopBadge
                }
            }
            .frame(height: 40)
            
            Spacer() // Pushes everything up, buttons are in overlay
        }
    }

    @ViewBuilder
    private func landscapeLayout(state: TimerState) -> some View {
        HStack(spacing: 48) {
            VStack(spacing: 0) {
                ZStack {
                    if !isComplete {
                        loopBadge
                    }
                }
                .frame(height: 40)
                
                Spacer().frame(height: 12)
                
                statusText(for: state)
                    .frame(height: 28)

                CircularTimerView(
                    progress: isComplete ? 1.0 : state.unpredictableProgress,
                    status: state.status,
                    rangeText: rangeText
                )
                .scaleEffect(0.8) // Shrink slightly for landscape
                
                Spacer().frame(height: 12)
                
                ZStack {
                    if isComplete {
                        Text("Went off after \(state.targetDuration.formattedDuration)")
                            .font(.caption)
                            .foregroundColor(.textSecondary)
                    } else {
                        Text("Surprise interval active")
                            .font(.caption)
                            .foregroundColor(.textMuted)
                    }
                }
                .frame(height: 20)
            }
            .frame(maxWidth: .infinity)
            
            // Right side is empty to leave room for buttons overlay if needed, 
            // or we could center the circle and let buttons overlay it.
            // For now, let's keep it centered.
            Color.clear.frame(maxWidth: .infinity)
        }
        .padding(.horizontal, 40)
    }
        .navigationBarBackButtonHidden(true)
        .onAppear {
            AnalyticsService.shared.screen(AnalyticsScreens.activeTimer)
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
