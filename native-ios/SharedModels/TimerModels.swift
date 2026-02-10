import Foundation
import ActivityKit

// MARK: - Sound Type

public enum SoundType: String, Codable, Sendable, CaseIterable {
    case intense
    case gentle

    /// Filename for UNNotificationSound (must match bundle resource)
    public var notificationSoundName: String {
        switch self {
        case .intense: return "alarm.mp3"
        case .gentle: return "gentle-chime.mp3"
        }
    }
}

// MARK: - Timer Configuration

/// Configuration for a random timer with all settings.
public struct TimerConfig: Codable, Sendable, Equatable {
    /// Minimum time in seconds
    public let minSeconds: Int
    /// Maximum time in seconds
    public let maxSeconds: Int
    /// How long the alarm should sound (seconds)
    public let alarmDuration: Int
    /// Hide remaining time (random mode)
    public let hiddenMode: Bool
    /// Auto-repeat timer after completion
    public let repeatEnabled: Bool
    /// Alarm sound type
    public let soundType: SoundType
    /// Volume level 0.0 - 1.0
    public let volume: Float
    /// Whether vibration is enabled
    public let vibrationEnabled: Bool

    public init(
        minSeconds: Int = 30,
        maxSeconds: Int = 120,
        alarmDuration: Int = 10,
        hiddenMode: Bool = false,
        repeatEnabled: Bool = false, // Default to LOOP OFF
        soundType: SoundType = .intense,
        volume: Float = 0.5, // Default to 50%
        vibrationEnabled: Bool = false
    ) {
        precondition(minSeconds >= 0, "Minimum seconds cannot be negative")
        precondition(maxSeconds >= minSeconds, "Maximum seconds must be >= minimum seconds")
        precondition(maxSeconds <= 300, "Maximum seconds cannot exceed 300 (5 minutes)")
        precondition(alarmDuration > 0, "Alarm duration must be positive")
        precondition(volume >= 0 && volume <= 1, "Volume must be between 0 and 1")

        self.minSeconds = minSeconds
        self.maxSeconds = maxSeconds
        self.alarmDuration = alarmDuration
        self.hiddenMode = hiddenMode
        self.repeatEnabled = repeatEnabled
        self.soundType = soundType
        self.volume = volume
        self.vibrationEnabled = vibrationEnabled
    }

    /// Minimum as TimeInterval
    public var minDuration: TimeInterval { TimeInterval(minSeconds) }

    /// Maximum as TimeInterval
    public var maxDuration: TimeInterval { TimeInterval(maxSeconds) }

    /// Alarm duration as TimeInterval
    public var alarmDurationInterval: TimeInterval { TimeInterval(alarmDuration) }

    public static let `default` = TimerConfig()

    public static let alarmDurationOptions = [5, 10, 15, 30, 60]
}

// MARK: - Timer Status

public enum TimerStatus: String, Codable, Sendable {
    case idle
    case running
    case paused
    case warning    // < 30 seconds remaining
    case danger     // < 10 seconds remaining
    case complete   // Timer finished, transitioning to alarm
    case alarm      // Alarm is playing
}

// MARK: - Timer State

/// Represents the current state of an active timer.
public struct TimerState: Codable, Sendable, Equatable {
    public let config: TimerConfig
    public let targetDuration: TimeInterval
    public let startedAt: Date
    public var remainingDuration: TimeInterval
    public var status: TimerStatus
    public var alarmTimeRemaining: TimeInterval
    public var alarmStartedAt: Date?

    public init(
        config: TimerConfig,
        targetDuration: TimeInterval,
        startedAt: Date = Date(),
        remainingDuration: TimeInterval? = nil,
        status: TimerStatus = .running,
        alarmTimeRemaining: TimeInterval = 0,
        alarmStartedAt: Date? = nil
    ) {
        self.config = config
        self.targetDuration = targetDuration
        self.startedAt = startedAt
        self.remainingDuration = remainingDuration ?? targetDuration
        self.status = status
        self.alarmTimeRemaining = alarmTimeRemaining
        self.alarmStartedAt = alarmStartedAt
    }

    public var progress: Double {
        guard targetDuration > 0 else { return 0 }
        return 1.0 - (remainingDuration / targetDuration)
    }

    public var isComplete: Bool {
        status == .complete || status == .alarm
    }

    public var isAlarmActive: Bool {
        status == .alarm && alarmTimeRemaining > 0
    }

    /// The date when the timer will complete
    public var endDate: Date {
        startedAt.addingTimeInterval(targetDuration)
    }

    /// Time remaining in seconds (for display)
    public var timeRemainingSeconds: Int {
        Int(max(0, remainingDuration))
    }
}

// MARK: - Live Activity Attributes

/// ActivityKit attributes for the timer Live Activity
public struct TimerActivityAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        public let status: TimerStatus
        public let remainingSeconds: Int

        public init(status: TimerStatus, remainingSeconds: Int) {
            self.status = status
            self.remainingSeconds = remainingSeconds
        }
    }

    /// Static properties - don't change during the activity
    public let timerName: String
    public let endDate: Date
    public let minSeconds: Int
    public let maxSeconds: Int

    public init(timerName: String = "Random Timer", endDate: Date, minSeconds: Int = 30, maxSeconds: Int = 120) {
        self.timerName = timerName
        self.endDate = endDate
        self.minSeconds = minSeconds
        self.maxSeconds = maxSeconds
    }

    /// Formatted range string (e.g., "30s - 2m")
    public var rangeText: String {
        let minFormatted = TimeInterval(minSeconds).formattedDuration
        let maxFormatted = TimeInterval(maxSeconds).formattedDuration
        return "\(minFormatted) - \(maxFormatted)"
    }
}

// MARK: - Helpers

extension TimeInterval {
    /// Format as "MM:SS"
    public var formattedMMSS: String {
        let totalSeconds = Int(max(0, self))
        let minutes = totalSeconds / 60
        let seconds = totalSeconds % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }

    /// Format as human-readable duration (e.g., "1m 30s", "45s")
    public var formattedDuration: String {
        let totalSeconds = Int(max(0, self))
        let mins = totalSeconds / 60
        let secs = totalSeconds % 60
        if mins > 0 {
            return secs > 0 ? "\(mins)m \(secs)s" : "\(mins)m"
        }
        return "\(secs)s"
    }

    /// Minutes component
    public var minutes: Int {
        Int(self) / 60
    }

    /// Seconds component
    public var seconds: Int {
        Int(self) % 60
    }
}

extension TimerStatus {
    /// Determines the status based on remaining time
    /// For random timers, we don't reveal warning/danger states - just running until complete
    public static func from(remainingSeconds: TimeInterval, currentStatus: TimerStatus) -> TimerStatus {
        if remainingSeconds <= 0 {
            return .complete
        }
        return currentStatus == .paused ? .paused : .running
    }
}
