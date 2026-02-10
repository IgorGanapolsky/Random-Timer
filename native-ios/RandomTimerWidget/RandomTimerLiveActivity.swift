import ActivityKit
import WidgetKit
import SwiftUI

/// Live Activity configuration for Random Timer
/// Displays timer status on Lock Screen and Dynamic Island
struct RandomTimerLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: TimerActivityAttributes.self) { context in
            // Lock Screen / Banner UI
            TimerLockScreenView(context: context)
                .activityBackgroundTint(Color(hex: "0F0A1A"))
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
                    ExpandedBottomActions()
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
                .frame(width: 44, height: 44)

            // Center: Timer information
            VStack(alignment: .leading, spacing: 4) {
                Text(context.attributes.timerName)
                    .font(.headline)
                    .foregroundColor(.white)

                if context.state.status == .complete || context.state.status == .alarm {
                    HStack(spacing: 4) {
                        Image(systemName: "bell.badge.fill")
                            .font(.caption)
                        Text("Time's up!")
                            .font(.subheadline)
                    }
                    .foregroundColor(statusColor)
                } else {
                    // Show range instead of countdown (preserves random timer surprise)
                    Text("Timer: \(context.attributes.rangeText)")
                        .font(.subheadline)
                        .foregroundColor(.white.opacity(0.7))
                }
            }

            Spacer()

            // Right: Visual progress indicator
            TimerProgressRing(
                status: context.state.status,
                progress: calculateProgress(context)
            )
            .frame(width: 40, height: 40)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }

    private var statusColor: Color {
        switch context.state.status {
        case .running: return Color(hex: "10B981")
        case .warning: return Color(hex: "F59E0B")
        case .danger, .complete, .alarm: return Color(hex: "EF4444")
        default: return .white
        }
    }

    /// Calculate visual progress (for animation purposes only)
    /// Note: For random timer, we show generic progress, not exact countdown
    private func calculateProgress(_ context: ActivityViewContext<TimerActivityAttributes>) -> Double {
        guard context.state.status == .running else { return 0 }

        // Show gentle pulsing animation instead of exact progress
        // This preserves the "random" nature while providing visual feedback
        let elapsed = Date().timeIntervalSince(context.attributes.endDate.addingTimeInterval(-Double(context.attributes.maxSeconds)))
        let maxDuration = Double(context.attributes.maxSeconds)
        guard maxDuration > 0 else { return 0 }

        let baseProgress = min(1.0, max(0.0, elapsed / maxDuration))

        // Add subtle pulse animation
        let pulseOffset = sin(Date().timeIntervalSinceReferenceDate * 2) * 0.05
        return min(1.0, max(0.0, baseProgress + pulseOffset))
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
                    Image(systemName: "bell.badge.fill")
                        .font(.title)
                        .foregroundColor(Color(hex: "EF4444"))
                        .symbolEffect(.bounce, options: .repeating)

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
    var body: some View {
        HStack(spacing: 16) {
            // Note: Button actions require App Intent implementation
            // This UI is ready for future interactivity

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
            // Background glow (only for non-compact)
            if !compact {
                Circle()
                    .fill(iconColor.opacity(0.2))
                    .blur(radius: 8)
            }

            // Icon with animation
            Image(systemName: iconName)
                .font(compact ? .caption : .title2)
                .foregroundColor(iconColor)
                .symbolEffect(.pulse, options: .repeating, value: status == .running)
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

/// Circular progress ring with smooth animation
struct TimerProgressRing: View {
    let status: TimerStatus
    let progress: Double

    @State private var animatedProgress: Double = 0

    var body: some View {
        ZStack {
            // Background ring
            Circle()
                .stroke(ringColor.opacity(0.2), lineWidth: 3)

            // Progress ring
            Circle()
                .trim(from: 0, to: animatedProgress)
                .stroke(
                    ringColor,
                    style: StrokeStyle(lineWidth: 3, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))
                .animation(.easeInOut(duration: 0.5), value: animatedProgress)

            // Center icon (for non-alarm states)
            if status != .complete && status != .alarm {
                Image(systemName: "timer")
                    .font(.caption2)
                    .foregroundColor(ringColor.opacity(0.7))
            } else {
                Image(systemName: "checkmark")
                    .font(.caption2)
                    .foregroundColor(ringColor)
            }
        }
        .onAppear {
            animatedProgress = progress
        }
        .onChange(of: progress) { _, newValue in
            animatedProgress = newValue
        }
        .accessibilityLabel("Timer progress")
        .accessibilityValue("\(Int(progress * 100)) percent")
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
/// Note: This requires proper App Intent setup in the main app
struct StopTimerIntent: LiveActivityIntent {
    static let title: LocalizedStringResource = "Stop Timer"
    static let description: IntentDescription = "Stops the currently running timer"

    func perform() async throws -> some IntentResult {
        // This will be handled by the main app through URL scheme or shared container
        // Implementation would trigger timer stop in TimerManager
        return .result()
    }
}

// MARK: - Previews

#Preview("Lock Screen - Running", as: .content, using: TimerActivityAttributes(
    timerName: "Random Timer",
    endDate: Date().addingTimeInterval(180),
    minSeconds: 60,
    maxSeconds: 180
)) {
    RandomTimerLiveActivity()
} contentStates: {
    TimerActivityAttributes.ContentState(status: .running, remainingSeconds: 120)
}

#Preview("Lock Screen - Alarm", as: .content, using: TimerActivityAttributes(
    timerName: "Random Timer",
    endDate: Date(),
    minSeconds: 60,
    maxSeconds: 180
)) {
    RandomTimerLiveActivity()
} contentStates: {
    TimerActivityAttributes.ContentState(status: .alarm, remainingSeconds: 0)
}

#Preview("Dynamic Island - Compact", as: .dynamicIsland(.compact), using: TimerActivityAttributes(
    timerName: "Random Timer",
    endDate: Date().addingTimeInterval(180),
    minSeconds: 60,
    maxSeconds: 180
)) {
    RandomTimerLiveActivity()
} contentStates: {
    TimerActivityAttributes.ContentState(status: .running, remainingSeconds: 120)
}

#Preview("Dynamic Island - Expanded", as: .dynamicIsland(.expanded), using: TimerActivityAttributes(
    timerName: "Random Timer",
    endDate: Date().addingTimeInterval(180),
    minSeconds: 60,
    maxSeconds: 180
)) {
    RandomTimerLiveActivity()
} contentStates: {
    TimerActivityAttributes.ContentState(status: .running, remainingSeconds: 120)
}
