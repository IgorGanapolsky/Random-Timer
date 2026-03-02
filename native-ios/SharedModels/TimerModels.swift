import Foundation
import ActivityKit

// MARK: - Sound Type

public enum SoundType: String, Codable, Sendable, CaseIterable {
    case intense
    case gentle
    case klaxon
    case whistle
    case buzzer
    case gong
    case airhorn
    case drumRoll
    case siren
    case bell

    /// Whether this sound requires Pro upgrade
    public var isPro: Bool {
        switch self {
        case .intense, .gentle: return false
        default: return true
        }
    }

    /// Free-tier sounds only
    public static var freeSounds: [SoundType] {
        allCases.filter { !$0.isPro }
    }

    /// Pro-tier sounds only
    public static var proSounds: [SoundType] {
        allCases.filter { $0.isPro }
    }

    /// Filename for UNNotificationSound (must match bundle resource)
    public var notificationSoundName: String {
        switch self {
        case .intense: return "alarm.mp3"
        case .gentle: return "gentle-chime.mp3"
        case .klaxon: return "klaxon.mp3"
        case .whistle: return "whistle.mp3"
        case .buzzer: return "buzzer.mp3"
        case .gong: return "gong.mp3"
        case .airhorn: return "airhorn.mp3"
        case .drumRoll: return "drum_roll.mp3"
        case .siren: return "siren.mp3"
        case .bell: return "bell.mp3"
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
        minSeconds: Int = 0,
        maxSeconds: Int = 60,
        alarmDuration: Int = 10,
        hiddenMode: Bool = false,
        repeatEnabled: Bool = false, // Default to LOOP OFF
        soundType: SoundType = .intense,
        volume: Float = 0.5, // Default to 50%
        vibrationEnabled: Bool = false
    ) {
        precondition(minSeconds >= 0, "Minimum seconds cannot be negative")
        precondition(maxSeconds >= minSeconds, "Maximum seconds must be >= minimum seconds")
        precondition(maxSeconds <= TimerConfig.maxSecondsPro, "Maximum seconds cannot exceed \(TimerConfig.maxSecondsPro)")
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

    public static let maxSecondsFree = 300
    public static let maxSecondsPro = 3600

    public static let `default` = TimerConfig()

    public static let alarmDurationOptions = [5, 10, 15, 30, 60]

    /// Returns a copy of this config with values clamped to the caller's Pro entitlement.
    /// Call this at deserialization time to enforce feature gating after subscription expiry.
    public func clamped(isPro: Bool) -> TimerConfig {
        let maxAllowed = isPro ? TimerConfig.maxSecondsPro : TimerConfig.maxSecondsFree
        let clampedMax = min(maxSeconds, maxAllowed)
        let clampedMin = min(minSeconds, clampedMax)
        let allowedSounds: [SoundType] = isPro ? SoundType.allCases : SoundType.freeSounds
        let clampedSound = allowedSounds.contains(soundType) ? soundType : .intense
        return TimerConfig(
            minSeconds: clampedMin,
            maxSeconds: clampedMax,
            alarmDuration: alarmDuration,
            hiddenMode: hiddenMode,
            repeatEnabled: repeatEnabled,
            soundType: clampedSound,
            volume: volume,
            vibrationEnabled: vibrationEnabled
        )
    }
}

// MARK: - Range Adjustment

/// Shared business rules for the "Goes Off In This Range" sliders.
///
/// UX requirement:
/// - Min/max must keep at least `minGapSeconds` between them.
/// - Dragging one thumb should "push/pull" the other thumb as needed, rather than blocking.
enum TimeRangeAdjuster {
    static let defaultMinSecondsLimit = 0
    static let defaultMaxSecondsLimit = TimerConfig.maxSecondsFree
    static let defaultMinGapSeconds = 30

    static func adjustForMinChange(
        currentMinSeconds: Int,
        currentMaxSeconds: Int,
        newMinSeconds: Int,
        minSecondsLimit: Int = defaultMinSecondsLimit,
        maxSecondsLimit: Int = defaultMaxSecondsLimit,
        minGapSeconds: Int = defaultMinGapSeconds
    ) -> (min: Int, max: Int) {
        precondition(minGapSeconds >= 0, "minGapSeconds must be >= 0")
        precondition(maxSecondsLimit >= minSecondsLimit, "maxSecondsLimit must be >= minSecondsLimit")

        var adjustedMinSeconds = Swift.min(
            Swift.max(newMinSeconds, minSecondsLimit),
            maxSecondsLimit - minGapSeconds
        )
        var adjustedMaxSeconds = Swift.min(
            Swift.max(currentMaxSeconds, minSecondsLimit + minGapSeconds),
            maxSecondsLimit
        )

        if adjustedMinSeconds > adjustedMaxSeconds - minGapSeconds {
            adjustedMaxSeconds = Swift.min(adjustedMinSeconds + minGapSeconds, maxSecondsLimit)
            adjustedMinSeconds = Swift.max(adjustedMaxSeconds - minGapSeconds, minSecondsLimit)
        }

        return (adjustedMinSeconds, adjustedMaxSeconds)
    }

    static func adjustForMaxChange(
        currentMinSeconds: Int,
        currentMaxSeconds: Int,
        newMaxSeconds: Int,
        minSecondsLimit: Int = defaultMinSecondsLimit,
        maxSecondsLimit: Int = defaultMaxSecondsLimit,
        minGapSeconds: Int = defaultMinGapSeconds
    ) -> (min: Int, max: Int) {
        precondition(minGapSeconds >= 0, "minGapSeconds must be >= 0")
        precondition(maxSecondsLimit >= minSecondsLimit, "maxSecondsLimit must be >= minSecondsLimit")

        var adjustedMaxSeconds = Swift.min(
            Swift.max(newMaxSeconds, minSecondsLimit + minGapSeconds),
            maxSecondsLimit
        )
        var adjustedMinSeconds = Swift.min(
            Swift.max(currentMinSeconds, minSecondsLimit),
            maxSecondsLimit - minGapSeconds
        )

        if adjustedMaxSeconds < adjustedMinSeconds + minGapSeconds {
            adjustedMinSeconds = Swift.max(adjustedMaxSeconds - minGapSeconds, minSecondsLimit)
            adjustedMaxSeconds = Swift.min(adjustedMinSeconds + minGapSeconds, maxSecondsLimit)
        }

        return (adjustedMinSeconds, adjustedMaxSeconds)
    }
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
    public var config: TimerConfig
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

    // MARK: - Sanitized Live Activity Properties
    // These prevent the lock screen from leaking timing information

    /// Remaining seconds for Live Activity — always 0 to prevent timing leak
    public var liveActivityRemainingSeconds: Int { 0 }

    /// End date for Live Activity — uses maxSeconds instead of actual targetDuration
    /// so observers cannot deduce the random duration from the progress ring
    public var liveActivityEndDate: Date {
        startedAt.addingTimeInterval(Double(config.maxSeconds))
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

    public init(timerName: String = "Random Tactical Timer", endDate: Date, minSeconds: Int = 30, maxSeconds: Int = 120) {
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

// MARK: - Entitlement Level

public enum EntitlementLevel: String, Codable, Sendable {
    case none
    case base
    case elite

    public var isPro: Bool {
        self != .none
    }
}
