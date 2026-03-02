import Foundation
import ActivityKit

// MARK: - Entitlement Level

public enum EntitlementLevel: Int, Codable, Sendable, Comparable {
    case none = 0
    case base = 1
    case elite = 2

    public static func < (lhs: EntitlementLevel, rhs: EntitlementLevel) -> Bool {
        return lhs.rawValue < rhs.rawValue
    }
}

// MARK: - Elite Configuration

public struct EliteConfig: Codable, Sendable, Equatable {
    public var aiCalloutsEnabled: Bool
    public var calloutFrequency: Double // Seconds between callouts
    public var calloutIntensity: Double // 0.0 to 1.0
    
    public init(aiCalloutsEnabled: Bool = false, calloutFrequency: Double = 5.0, calloutIntensity: Double = 0.5) {
        self.aiCalloutsEnabled = aiCalloutsEnabled
        self.calloutFrequency = calloutFrequency
        self.calloutIntensity = calloutIntensity
    }
    
    public static let `default` = EliteConfig()
}

// MARK: - Sound Type

public enum SoundType: String, Codable, Sendable, CaseIterable {
    case intense, gentle, klaxon, whistle, buzzer, gong, airhorn, drumRoll, siren, bell

    public var isPro: Bool {
        switch self {
        case .intense, .gentle: return false
        default: return true
        }
    }

    public static var freeSounds: [SoundType] { allCases.filter { !$0.isPro } }
    public static var proSounds: [SoundType] { allCases.filter { $0.isPro } }

    public var notificationSoundName: String {
        switch self {
        case .intense: return "alarm.mp3"
        case .gentle: return "gentle-chime.mp3"
        default: return "\(self.rawValue).mp3"
        }
    }
}

// MARK: - Timer Configuration

public struct TimerConfig: Codable, Sendable, Equatable {
    public let minSeconds: Int
    public let maxSeconds: Int
    public let alarmDuration: Int
    public let hiddenMode: Bool
    public let repeatEnabled: Bool
    public let soundType: SoundType
    public let volume: Float
    public let vibrationEnabled: Bool
    public var eliteConfig: EliteConfig

    public init(
        minSeconds: Int = 0,
        maxSeconds: Int = 60,
        alarmDuration: Int = 10,
        hiddenMode: Bool = false,
        repeatEnabled: Bool = false,
        soundType: SoundType = .intense,
        volume: Float = 0.5,
        vibrationEnabled: Bool = false,
        eliteConfig: EliteConfig = .default
    ) {
        self.minSeconds = minSeconds
        self.maxSeconds = maxSeconds
        self.alarmDuration = alarmDuration
        self.hiddenMode = hiddenMode
        self.repeatEnabled = repeatEnabled
        self.soundType = soundType
        self.volume = volume
        self.vibrationEnabled = vibrationEnabled
        self.eliteConfig = eliteConfig
    }

    public var minDuration: TimeInterval { TimeInterval(minSeconds) }
    public var maxDuration: TimeInterval { TimeInterval(maxSeconds) }
    public var alarmDurationInterval: TimeInterval { TimeInterval(alarmDuration) }

    public static let maxSecondsFree = 300
    public static let maxSecondsPro = 3600
    public static let `default` = TimerConfig()
    public static let alarmDurationOptions = [5, 10, 15, 30, 60]

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
            vibrationEnabled: vibrationEnabled,
            eliteConfig: eliteConfig
        )
    }
}

// MARK: - Range Adjustment

enum TimeRangeAdjuster {
    static let defaultMinGapSeconds = 30

    static func adjustForMinChange(currentMinSeconds: Int, currentMaxSeconds: Int, newMinSeconds: Int, maxSecondsLimit: Int) -> (min: Int, max: Int) {
        let adjustedMin = min(max(newMinSeconds, 0), maxSecondsLimit - defaultMinGapSeconds)
        let adjustedMax = max(currentMaxSeconds, adjustedMin + defaultMinGapSeconds)
        return (adjustedMin, min(adjustedMax, maxSecondsLimit))
    }

    static func adjustForMaxChange(currentMinSeconds: Int, currentMaxSeconds: Int, newMaxSeconds: Int, maxSecondsLimit: Int) -> (min: Int, max: Int) {
        let adjustedMax = min(max(newMaxSeconds, defaultMinGapSeconds), maxSecondsLimit)
        let adjustedMin = min(currentMinSeconds, adjustedMax - defaultMinGapSeconds)
        return (max(adjustedMin, 0), adjustedMax)
    }
}

// MARK: - Timer Status

public enum TimerStatus: String, Codable, Sendable {
    case idle, running, paused, warning, danger, complete, alarm
}

// MARK: - Timer State

public struct TimerState: Codable, Sendable, Equatable {
    public var config: TimerConfig
    public var targetDuration: TimeInterval
    public var startedAt: Date
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
    
    public var endDate: Date { startedAt.addingTimeInterval(targetDuration) }
    public var isComplete: Bool { status == .complete || status == .alarm }
    
    public var liveActivityRemainingSeconds: Int { Int(max(0, remainingDuration)) }
    public var liveActivityEndDate: Date { startedAt.addingTimeInterval(targetDuration) }
}

// MARK: - Activity Attributes

public struct TimerActivityAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        public var status: TimerStatus
        public var remainingSeconds: Int
        public init(status: TimerStatus, remainingSeconds: Int) {
            self.status = status
            self.remainingSeconds = remainingSeconds
        }
    }
    public var timerName: String
    public var endDate: Date
    public let minSeconds: Int
    public let maxSeconds: Int
    
    public init(timerName: String, endDate: Date, minSeconds: Int, maxSeconds: Int) {
        self.timerName = timerName
        self.endDate = endDate
        self.minSeconds = minSeconds
        self.maxSeconds = maxSeconds
    }
}

public enum TimerAction: String, Codable {
    case stop, pause, resume
}

public let timerAppGroupSuite = "group.com.iganapolsky.randomtimer"
public let timerPendingActionKey = "pendingTimerAction"

// MARK: - Helpers

extension TimeInterval {
    public var formattedMMSS: String {
        let totalSeconds = Int(max(0, self))
        return String(format: "%02d:%02d", totalSeconds / 60, totalSeconds % 60)
    }

    public var formattedDuration: String {
        let totalSeconds = Int(max(0, self))
        let mins = totalSeconds / 60
        let secs = totalSeconds % 60
        return mins > 0 ? (secs > 0 ? "\(mins)m \(secs)s" : "\(mins)m") : "\(secs)s"
    }
}

extension TimerStatus {
    public static func from(remainingSeconds: TimeInterval, currentStatus: TimerStatus) -> TimerStatus {
        if remainingSeconds <= 0 { return .complete }
        return currentStatus == .paused ? .paused : .running
    }
}
