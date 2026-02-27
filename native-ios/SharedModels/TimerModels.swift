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

    public var isPro: Bool {
        switch self {
        case .intense, .gentle: return false
        default: return true
        }
    }

    public static var freeSounds: [SoundType] {
        allCases.filter { !$0.isPro }
    }

    public static var proSounds: [SoundType] {
        allCases.filter { $0.isPro }
    }

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
}

// MARK: - Range Adjustment

enum TimeRangeAdjuster {
    static func adjustForMinChange(currentMinSeconds: Int, currentMaxSeconds: Int, newMinSeconds: Int, maxSecondsLimit: Int) -> (min: Int, max: Int) {
        let minGap = 30
        let adjustedMin = min(max(newMinSeconds, 0), maxSecondsLimit - minGap)
        let adjustedMax = max(currentMaxSeconds, adjustedMin + minGap)
        return (adjustedMin, min(adjustedMax, maxSecondsLimit))
    }

    static func adjustForMaxChange(currentMinSeconds: Int, currentMaxSeconds: Int, newMaxSeconds: Int, maxSecondsLimit: Int) -> (min: Int, max: Int) {
        let minGap = 30
        let adjustedMax = min(max(newMaxSeconds, minGap), maxSecondsLimit)
        let adjustedMin = min(currentMinSeconds, adjustedMax - minGap)
        return (max(adjustedMin, 0), adjustedMax)
    }
}

// MARK: - Activity Attributes (REQUIRED FOR BUILD)

public struct TimerActivityAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        public let status: String
        public let remainingSeconds: Int
    }
    public let timerName: String
}

public enum TimerAction: String, Codable {
    case stop, pause, resume
}
