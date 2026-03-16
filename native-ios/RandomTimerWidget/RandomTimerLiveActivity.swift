import ActivityKit
import WidgetKit
import SwiftUI

/// Live Activity configuration for Random Tactical Timer
/// Displays timer status on Lock Screen and Dynamic Island
struct RandomTimerLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: TimerActivityAttributes.self) { context in
            // Lock Screen / Banner UI
            TimerLockScreenView(context: context)
                .activityBackgroundTint(Color.black.opacity(0.4))
                .activitySystemActionForegroundColor(.white)

        } dynamicIsland: { context in
            DynamicIsland {
                // Expanded UI (long press on Dynamic Island)
                DynamicIslandExpandedRegion(.leading) {
                    TimerIconView(status: context.state.status)
                        .frame(width: 40, height: 40)
                }

                DynamicIslandExpandedRegion(.trailing) {
                    TimerStatusBadge(status: context.state.status)
                }

                DynamicIslandExpandedRegion(.center) {
                    ExpandedTimerView(context: context)
                }

                DynamicIslandExpandedRegion(.bottom) {
                    ExpandedBottomActions(status: context.state.status)
                }

            } compactLeading: {
                // Compact view - left side of island
                TimerIconView(status: context.state.status, compact: true)
                    .frame(width: 20, height: 20)

            } compactTrailing: {
                // Compact view - right side of island
                // Show range for random timer (don't reveal exact time)
                Text(formatCompactRange(context.attributes))
                    .font(.caption2.monospacedDigit())
                    .foregroundColor(.white.opacity(0.9))

            } minimal: {
                // Minimal view - smallest representation
                TimerIconView(status: context.state.status, compact: true)
                    .frame(width: 16, height: 16)
            }
        }
    }

    /// Format range for compact display
    private func formatCompactRange(_ attributes: TimerActivityAttributes) -> String {
        let minText = formatCompactTime(attributes.minSeconds)
        let maxText = formatCompactTime(attributes.maxSeconds)
        return "\(minText)-\(maxText)"
    }

    private func formatCompactTime(_ seconds: Int) -> String {
        if seconds >= 60 {
            let mins = seconds / 60
            return "\(mins)m"
        }
        return "\(seconds)s"
    }
}

// MARK: - Lock Screen View

/// Main Lock Screen Live Activity view
/// Beautiful glassmorphic design with animated elements
struct TimerLockScreenView: View {
    let context: ActivityViewContext<TimerActivityAttributes>

    var body: some View {
        HStack(spacing: 16) {
            // Left: Animated timer icon with glow
            TimerIconView(status: context.state.status)
                .frame(width: 48, height: 48)

            // Center: Timer information
            VStack(alignment: .leading, spacing: 6) {
                Text(context.attributes.timerName)
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(.white)

                if context.state.status == .complete || context.state.status == .alarm {
                    HStack(spacing: 6) {
                        Image(systemName: "bell.badge.fill")
                            .font(.system(size: 13, weight: .medium))
                        Text("Time's up!")
                            .font(.system(size: 15, weight: .medium))
                    }
                    .foregroundColor(statusColor)
                } else {
                    // Show range instead of countdown (preserves random timer surprise)
                    Text("Timer: \(context.attributes.rangeText)")
                        .font(.system(size: 15, weight: .regular))
                        .foregroundColor(.white.opacity(0.85))
                }
            }

            Spacer()

            // Right: Decorative progress ring with random animation
            // Uses multi-frequency sine waves so progress looks alive
            // but doesn't correlate with actual timer progress
            RandomProgressRing(status: context.state.status)
                .frame(width: 44, height: 44)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 14)
    }

    private var statusColor: Color {
        switch context.state.status {
        case .running: return Color(hex: "10B981")
        case .warning: return Color(hex: "F59E0B")
        case .danger, .complete, .alarm: return Color(hex: "EF4444")
        default: return .white
        }
    }

}

// MARK: - Dynamic Island Expanded View

/// Expanded Dynamic Island center content
struct ExpandedTimerView: View {
    let context: ActivityViewContext<TimerActivityAttributes>

    var body: some View {
        VStack(spacing: 12) {
            Text(context.attributes.timerName)
                .font(.headline)
                .foregroundColor(.white)

            if context.state.status == .complete || context.state.status == .alarm {
                // Alarm state
                VStack(spacing: 6) {
                    if #available(iOSApplicationExtension 18.0, *) {
                        Image(systemName: "bell.badge.fill")
                            .font(.title)
                            .foregroundColor(Color(hex: "EF4444"))
                            .symbolEffect(.bounce, options: .repeating)
                    } else {
                        Image(systemName: "bell.badge.fill")
                            .font(.title)
                            .foregroundColor(Color(hex: "EF4444"))
                    }

                    Text("Time's up!")
                        .font(.title3.bold())
                        .foregroundColor(Color(hex: "EF4444"))
                }
            } else {
                // Running state
                VStack(spacing: 8) {
                    Text("Timer Active")
                        .font(.subheadline)
                        .foregroundColor(.white.opacity(0.7))

                    Text(context.attributes.rangeText)
                        .font(.title2.bold().monospacedDigit())
                        .foregroundColor(Color(hex: "10B981"))

                    Text("Random interval")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.5))
                }
            }
        }
        .padding(.vertical, 8)
    }
}

/// Expanded Dynamic Island bottom action buttons
struct ExpandedBottomActions: View {
    let status: TimerStatus

    var body: some View {
        HStack(spacing: 12) {
            if status == .running {
                Button(intent: PauseTimerIntent()) {
                    Label("Pause", systemImage: "pause.fill")
                        .font(.caption.bold())
                        .foregroundColor(.white)
                }
                .buttonStyle(.borderedProminent)
                .tint(Color(hex: "F59E0B"))
                .clipShape(Capsule())
            } else if status == .paused {
                Button(intent: ResumeTimerIntent()) {
                    Label("Resume", systemImage: "play.fill")
                        .font(.caption.bold())
                        .foregroundColor(.white)
                }
                .buttonStyle(.borderedProminent)
                .tint(Color(hex: "10B981"))
                .clipShape(Capsule())
            }

            Button(intent: StopTimerIntent()) {
                Label("Stop", systemImage: "stop.fill")
                    .font(.caption.bold())
                    .foregroundColor(.white)
            }
            .buttonStyle(.borderedProminent)
            .tint(Color(hex: "EF4444"))
            .clipShape(Capsule())
        }
        .padding(.bottom, 8)
    }
}

// MARK: - Reusable Components

/// Animated timer icon with status-based styling
struct TimerIconView: View {
    let status: TimerStatus
    var compact: Bool = false

    var body: some View {
        ZStack {
            // Background circle with glow
            if !compact {
                Circle()
                    .fill(iconColor.opacity(0.25))
                    .frame(width: 48, height: 48)

                Circle()
                    .fill(iconColor.opacity(0.15))
                    .frame(width: 56, height: 56)
                    .blur(radius: 6)
            }

            // Icon with animation
            if #available(iOSApplicationExtension 18.0, *) {
                Image(systemName: iconName)
                    .font(.system(size: compact ? 14 : 22, weight: .semibold))
                    .foregroundColor(iconColor)
                    .symbolEffect(.pulse, options: .repeating, value: status == .running)
            } else {
                Image(systemName: iconName)
                    .font(.system(size: compact ? 14 : 22, weight: .semibold))
                    .foregroundColor(iconColor)
                    .symbolEffect(.pulse, value: status == .running)
            }
        }
        .accessibilityLabel(accessibilityLabel)
    }

    private var iconName: String {
        switch status {
        case .complete, .alarm:
            return "bell.badge.fill"
        case .running:
            return "timer"
        case .paused:
            return "pause.circle.fill"
        default:
            return "timer"
        }
    }

    private var iconColor: Color {
        switch status {
        case .running: return Color(hex: "10B981")
        case .warning: return Color(hex: "F59E0B")
        case .danger, .complete, .alarm: return Color(hex: "EF4444")
        case .paused: return Color(hex: "A1A1AA")
        default: return .white
        }
    }

    private var accessibilityLabel: String {
        switch status {
        case .running: return "Timer running"
        case .paused: return "Timer paused"
        case .complete, .alarm: return "Timer complete"
        default: return "Timer"
        }
    }
}

/// Status badge for Dynamic Island expanded view
struct TimerStatusBadge: View {
    let status: TimerStatus

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(statusColor)
                .frame(width: 6, height: 6)

            Text(statusText)
                .font(.caption2.bold())
                .foregroundColor(.white)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(statusColor.opacity(0.2))
        )
        .accessibilityLabel("\(statusText) status")
    }

    private var statusText: String {
        switch status {
        case .running: return "Active"
        case .paused: return "Paused"
        case .complete, .alarm: return "Complete"
        default: return "Ready"
        }
    }

    private var statusColor: Color {
        switch status {
        case .running: return Color(hex: "10B981")
        case .warning: return Color(hex: "F59E0B")
        case .danger, .complete, .alarm: return Color(hex: "EF4444")
        default: return .white
        }
    }
}

/// Decorative circular progress ring with pseudo-random animation.
/// Uses overlapping sine waves so the fill level wanders unpredictably
/// without correlating to real timer progress.
struct RandomProgressRing: View {
    let status: TimerStatus

    var body: some View {
        ZStack {
            // Background ring
            Circle()
                .stroke(ringColor.opacity(0.3), lineWidth: 4)

            // Decorative fill — random-looking via multi-frequency sine
            Circle()
                .trim(from: 0, to: decorativeProgress)
                .stroke(
                    ringColor,
                    style: StrokeStyle(lineWidth: 4, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))
                .shadow(color: ringColor.opacity(0.4), radius: 3)

            // Center icon
            if status == .complete || status == .alarm {
                Image(systemName: "checkmark")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(ringColor)
            } else {
                Image(systemName: "timer")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(ringColor.opacity(0.9))
            }
        }
        .accessibilityLabel("Timer active")
    }

    /// Pseudo-random progress using overlapping sine waves.
    /// Oscillates between ~0.15 and ~0.85 — looks alive but reveals nothing.
    private var decorativeProgress: Double {
        guard status == .running || status == .warning || status == .danger else {
            return status == .complete || status == .alarm ? 1.0 : 0.0
        }
        let t = Date().timeIntervalSinceReferenceDate
        let wave1 = sin(t * 0.7) * 0.20
        let wave2 = sin(t * 1.3) * 0.10
        let wave3 = sin(t * 2.1) * 0.05
        return min(0.85, max(0.15, 0.50 + wave1 + wave2 + wave3))
    }

    private var ringColor: Color {
        switch status {
        case .running: return Color(hex: "10B981")
        case .warning: return Color(hex: "F59E0B")
        case .danger, .complete, .alarm: return Color(hex: "EF4444")
        default: return .white
        }
    }
}

// MARK: - App Intent for Interactive Buttons

import AppIntents

/// App Intent for stopping the timer from Live Activity
struct StopTimerIntent: LiveActivityIntent {
    static let title: LocalizedStringResource = "Stop Timer"
    static let description: IntentDescription = "Stops the currently running timer"

    func perform() async throws -> some IntentResult {
        let defaults = UserDefaults(suiteName: timerAppGroupSuite)
        defaults?.set(TimerAction.stop.rawValue, forKey: timerPendingActionKey)
        return .result()
    }
}

/// App Intent for pausing the timer from Live Activity
struct PauseTimerIntent: LiveActivityIntent {
    static let title: LocalizedStringResource = "Pause Timer"
    static let description: IntentDescription = "Pauses the currently running timer"

    func perform() async throws -> some IntentResult {
        let defaults = UserDefaults(suiteName: timerAppGroupSuite)
        defaults?.set(TimerAction.pause.rawValue, forKey: timerPendingActionKey)
        return .result()
    }
}

/// App Intent for resuming the timer from Live Activity
struct ResumeTimerIntent: LiveActivityIntent {
    static let title: LocalizedStringResource = "Resume Timer"
    static let description: IntentDescription = "Resumes the paused timer"

    func perform() async throws -> some IntentResult {
        let defaults = UserDefaults(suiteName: timerAppGroupSuite)
        defaults?.set(TimerAction.resume.rawValue, forKey: timerPendingActionKey)
        return .result()
    }
}

// MARK: - Previews

#Preview("Lock Screen - Running", as: .content, using: TimerActivityAttributes(
    timerName: "Random Tactical Timer",
    endDate: Date().addingTimeInterval(180),
    minSeconds: 60,
    maxSeconds: 180
)) {
    RandomTimerLiveActivity()
} contentStates: {
    TimerActivityAttributes.ContentState(status: .running, remainingSeconds: 120)
}

#Preview("Lock Screen - Alarm", as: .content, using: TimerActivityAttributes(
    timerName: "Random Tactical Timer",
    endDate: Date(),
    minSeconds: 60,
    maxSeconds: 180
)) {
    RandomTimerLiveActivity()
} contentStates: {
    TimerActivityAttributes.ContentState(status: .alarm, remainingSeconds: 0)
}

#Preview("Dynamic Island - Compact", as: .dynamicIsland(.compact), using: TimerActivityAttributes(
    timerName: "Random Tactical Timer",
    endDate: Date().addingTimeInterval(180),
    minSeconds: 60,
    maxSeconds: 180
)) {
    RandomTimerLiveActivity()
} contentStates: {
    TimerActivityAttributes.ContentState(status: .running, remainingSeconds: 120)
}

#Preview("Dynamic Island - Expanded", as: .dynamicIsland(.expanded), using: TimerActivityAttributes(
    timerName: "Random Tactical Timer",
    endDate: Date().addingTimeInterval(180),
    minSeconds: 60,
    maxSeconds: 180
)) {
    RandomTimerLiveActivity()
} contentStates: {
    TimerActivityAttributes.ContentState(status: .running, remainingSeconds: 120)
}
