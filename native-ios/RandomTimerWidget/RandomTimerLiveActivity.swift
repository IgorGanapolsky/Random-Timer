import ActivityKit
import WidgetKit
import SwiftUI

struct RandomTimerLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: TimerActivityAttributes.self) { context in
            // Lock Screen / Banner UI
            LockScreenView(context: context)
                .activityBackgroundTint(Color(hex: "0F0A1A"))
                .activitySystemActionForegroundColor(.white)

        } dynamicIsland: { context in
            DynamicIsland {
                // Expanded UI
                DynamicIslandExpandedRegion(.center) {
                    ExpandedTimerView(context: context)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    HStack(spacing: 16) {
                        Button(intent: StopTimerIntent()) {
                            Label("Stop", systemImage: "stop.fill")
                                .font(.caption)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.red)
                    }
                }
            } compactLeading: {
                Image(systemName: statusIcon(for: context.state.status))
                    .foregroundColor(statusColor(for: context.state.status))
            } compactTrailing: {
                // Show range instead of countdown (random timer - user shouldn't know when)
                Text(context.attributes.rangeText)
                    .font(.caption2)
                    .foregroundColor(.white)
            } minimal: {
                Image(systemName: "timer")
                    .foregroundColor(statusColor(for: context.state.status))
            }
        }
    }

    private func statusIcon(for status: TimerStatus) -> String {
        switch status {
        case .complete, .alarm: return "bell.badge.fill"
        default: return "timer"
        }
    }

    private func statusColor(for status: TimerStatus) -> Color {
        switch status {
        case .running: return Color(hex: "10B981")
        case .warning: return Color(hex: "F59E0B")
        case .danger, .complete, .alarm: return Color(hex: "EF4444")
        default: return .white
        }
    }
}

// MARK: - Lock Screen View

struct LockScreenView: View {
    let context: ActivityViewContext<TimerActivityAttributes>

    var body: some View {
        HStack(spacing: 16) {
            // Timer icon
            Image(systemName: (context.state.status == .complete || context.state.status == .alarm) ? "bell.badge.fill" : "timer")
                .font(.title2)
                .foregroundColor(statusColor)

            VStack(alignment: .leading, spacing: 4) {
                Text(context.attributes.timerName)
                    .font(.headline)
                    .foregroundColor(.white)

                if context.state.status == .complete || context.state.status == .alarm {
                    Text("Time's up!")
                        .font(.subheadline)
                        .foregroundColor(statusColor)
                } else {
                    // Show range instead of countdown (random timer - user shouldn't know when)
                    Text("Goes off between \(context.attributes.rangeText)")
                        .font(.subheadline)
                        .foregroundColor(.white.opacity(0.8))
                }
            }

            Spacer()

            // Timer icon (no progress ring - random timer shouldn't show progress)
            Image(systemName: "timer")
                .font(.title)
                .foregroundColor(statusColor)
        }
        .padding()
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

// MARK: - Expanded View

struct ExpandedTimerView: View {
    let context: ActivityViewContext<TimerActivityAttributes>

    var body: some View {
        VStack(spacing: 8) {
            Text(context.attributes.timerName)
                .font(.headline)

            if context.state.status == .complete || context.state.status == .alarm {
                Text("Time's up!")
                    .font(.title)
                    .foregroundColor(Color(hex: "EF4444"))
            } else {
                Text("Timer Running")
                    .font(.title2)
                    .foregroundColor(.white)
                Text(context.attributes.rangeText)
                    .font(.headline)
                    .foregroundColor(.white.opacity(0.7))
            }
        }
    }
}

// MARK: - App Intent for Button Actions

import AppIntents

struct StopTimerIntent: LiveActivityIntent {
    static let title: LocalizedStringResource = "Stop Timer"

    func perform() async throws -> some IntentResult {
        // This will be handled by the main app
        return .result()
    }
}

// MARK: - Preview

#Preview("Lock Screen", as: .content, using: TimerActivityAttributes(endDate: Date().addingTimeInterval(300))) {
    RandomTimerLiveActivity()
} contentStates: {
    TimerActivityAttributes.ContentState(status: .running, remainingSeconds: 150)
    TimerActivityAttributes.ContentState(status: .warning, remainingSeconds: 25)
    TimerActivityAttributes.ContentState(status: .danger, remainingSeconds: 5)
    TimerActivityAttributes.ContentState(status: .complete, remainingSeconds: 0)
}
