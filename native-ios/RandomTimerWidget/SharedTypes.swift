import Foundation
import ActivityKit
import SwiftUI

// MARK: - Timer Status

public enum TimerStatus: String, Codable, Hashable {
    case idle
    case running
    case paused
    case warning
    case danger
    case complete
    case alarm
}

// MARK: - Live Activity Attributes

public struct TimerActivityAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        public let status: TimerStatus
        public let remainingSeconds: Int

        public init(status: TimerStatus, remainingSeconds: Int) {
            self.status = status
            self.remainingSeconds = remainingSeconds
        }
    }

    public let timerName: String
    public let endDate: Date
    public let minSeconds: Int
    public let maxSeconds: Int

    public init(timerName: String = "Random Tactical Timer", endDate: Date, minSeconds: Int = 5, maxSeconds: Int = 30) {
        self.timerName = timerName
        self.endDate = endDate
        self.minSeconds = minSeconds
        self.maxSeconds = maxSeconds
    }

    /// Formatted range text (e.g., "30s - 2m")
    public var rangeText: String {
        let minText = formatSeconds(minSeconds)
        let maxText = formatSeconds(maxSeconds)
        return "\(minText) - \(maxText)"
    }

    private func formatSeconds(_ seconds: Int) -> String {
        if seconds >= 60 {
            let mins = seconds / 60
            let secs = seconds % 60
            return secs > 0 ? "\(mins)m \(secs)s" : "\(mins)m"
        } else {
            return "\(seconds)s"
        }
    }
}

// MARK: - Live Activity Action Signaling

/// Actions that can be triggered from Live Activity intents via shared App Group UserDefaults
public enum TimerAction: String, Codable {
    case stop
    case pause
    case resume
}

/// Shared App Group suite name for cross-process communication
public let timerAppGroupSuite = "group.com.iganapolsky.randomtimer"

/// UserDefaults key for the pending timer action
public let timerPendingActionKey = "pendingTimerAction"

// MARK: - Color Extension

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
