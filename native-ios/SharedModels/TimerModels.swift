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
        repeatEnabled: Bool = false,
        soundType: SoundType = .intense,
        volume: Float = 0.5,
        vibrationEnabled: Bool = false
    ) {
        self.minSeconds = minSeconds
        self.maxSeconds = maxSeconds
        self.alarmDuration = alarmDuration
        self.hiddenMode = hiddenMode
        self.repeatEnabled = repeatEnabled
        self.soundType = soundType
        self.volume = volume
        self.vibrationEnabled = vibrationEnabled
    }

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
            vibrationEnabled: vibrationEnabled
        )
    }
}

// MARK: - Range Adjustment

enum TimeRangeAdjuster {
    static let defaultMinGapSeconds = 30

    static func adjustForMinChange(
        currentMinSeconds: Int,
        currentMaxSeconds: Int,
        newMinSeconds: Int,
        maxSecondsLimit: Int,
        minGapSeconds: Int = defaultMinGapSeconds
    ) -> (min: Int, max: Int) {
        let adjustedMin = min(max(newMinSeconds, 0), maxSecondsLimit - minGapSeconds)
        var adjustedMax = max(currentMaxSeconds, adjustedMin + minGapSeconds)
        adjustedMax = min(adjustedMax, maxSecondsLimit)
        return (adjustedMin, adjustedMax)
    }

    static func adjustForMaxChange(
        currentMinSeconds: Int,
        currentMaxSeconds: Int,
        newMaxSeconds: Int,
        maxSecondsLimit: Int,
        minGapSeconds: Int = defaultMinGapSeconds
    ) -> (min: Int, max: Int) {
        let adjustedMax = min(max(newMaxSeconds, minGapSeconds), maxSecondsLimit)
        var adjustedMin = min(currentMinSeconds, adjustedMax - minGapSeconds)
        adjustedMin = max(adjustedMin, 0)
        return (adjustedMin, adjustedMax)
    }
}

public enum TimerStatus: String, Codable, Sendable {
    case idle, running, paused, complete, alarm
}

public struct TimerState: Codable, Sendable, Equatable {
    public var config: TimerConfig
    public let targetDuration: TimeInterval
    public let startedAt: Date
    public var remainingDuration: TimeInterval
    public var status: TimerStatus

    public init(config: TimerConfig, targetDuration: TimeInterval, startedAt: Date = Date(), remainingDuration: TimeInterval? = nil, status: TimerStatus = .running) {
        self.config = config
        self.targetDuration = targetDuration
        self.startedAt = startedAt
        self.remainingDuration = remainingDuration ?? targetDuration
        self.status = status
    }
}

extension TimeInterval {
    public var formattedDuration: String {
        let totalSeconds = Int(max(0, self))
        let mins = totalSeconds / 60
        let secs = totalSeconds % 60
        if mins > 0 {
            return secs > 0 ? "\(mins)m \(secs)s" : "\(mins)m"
        }
        return "\(secs)s"
    }
}
