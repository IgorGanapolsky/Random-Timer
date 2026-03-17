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

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        let rawValue = try container.decode(String.self)
        guard let soundType = Self.fromLoose(rawValue) else {
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Unknown sound type: \(rawValue)"
            )
        }
        self = soundType
    }

    static func fromLoose(_ rawValue: String) -> SoundType? {
        let normalized = rawValue
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased()
            .replacingOccurrences(of: "_", with: "")
            .replacingOccurrences(of: "-", with: "")
            .replacingOccurrences(of: " ", with: "")

        switch normalized {
        case "intense": return .intense
        case "gentle": return .gentle
        case "klaxon": return .klaxon
        case "whistle": return .whistle
        case "buzzer": return .buzzer
        case "gong": return .gong
        case "airhorn": return .airhorn
        case "drumroll": return .drumRoll
        case "siren": return .siren
        case "bell": return .bell
        default: return nil
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
    /// Whether to use the extended 60-minute range (Pro only)
    public let useExtendedRange: Bool
    /// Whether AI voice callouts are enabled (Elite only)
    public let voiceEnabled: Bool
    /// How many rounds to loop for (0 = infinite). Pro only feature.
    public let repeatRounds: Int

    public init(
        minSeconds: Int = 0,
        maxSeconds: Int = 300,
        alarmDuration: Int = 10,
        hiddenMode: Bool = false,
        repeatEnabled: Bool = false, // Default to LOOP OFF
        soundType: SoundType = .intense,
        volume: Float = 0.5, // Default to 50%
        vibrationEnabled: Bool = false,
        useExtendedRange: Bool = false,
        voiceEnabled: Bool = true,
        repeatRounds: Int = 0
    ) {
        precondition(minSeconds >= 0, "Minimum seconds cannot be negative")
        precondition(maxSeconds >= minSeconds, "Maximum seconds must be >= minimum seconds")
        let maxPro = TimerConfig.maxSecondsPro
        precondition(maxSeconds <= maxPro, "Maximum seconds cannot exceed \(maxPro)")
        precondition(alarmDuration > 0, "Alarm duration must be positive")
        precondition(volume >= 0 && volume <= 1, "Volume must be between 0 and 1")
        precondition(repeatRounds >= 0, "Repeat rounds cannot be negative")

        self.minSeconds = minSeconds
        self.maxSeconds = maxSeconds
        self.alarmDuration = alarmDuration
        self.hiddenMode = hiddenMode
        self.repeatEnabled = repeatEnabled
        self.soundType = soundType
        self.volume = volume
        self.vibrationEnabled = vibrationEnabled
        self.useExtendedRange = useExtendedRange
        self.voiceEnabled = voiceEnabled
        self.repeatRounds = repeatRounds
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

    fileprivate enum DecodingKeys: String, CodingKey {
        case minSeconds
        case maxSeconds
        case alarmDuration
        case hiddenMode
        case repeatEnabled
        case soundType
        case volume
        case vibrationEnabled
        case useExtendedRange
        case voiceEnabled
        case repeatRounds

        // Legacy / compatibility keys
        case minDuration
        case maxDuration
        case min_seconds
        case max_seconds
        case min_time
        case max_time
        case alarm_duration
        case hidden_mode
        case repeat_enabled
        case loopEnabled
        case sound_type
        case alarmSound
        case sound
        case soundVolume
        case vibration
        case vibration_enabled
        case voice_callouts_enabled
    }

    private enum EncodingKeys: String, CodingKey {
        case minSeconds
        case maxSeconds
        case alarmDuration
        case hiddenMode
        case repeatEnabled
        case soundType
        case volume
        case vibrationEnabled
        case useExtendedRange
        case voiceEnabled
        case repeatRounds
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: DecodingKeys.self)

        let rawMin = container.decodeFirstInt(
            forKeys: [.minSeconds, .minDuration, .min_seconds, .min_time],
            defaultValue: 0
        )
        let rawMax = container.decodeFirstInt(
            forKeys: [.maxSeconds, .maxDuration, .max_seconds, .max_time],
            defaultValue: 300
        )
        let rawAlarm = container.decodeFirstInt(
            forKeys: [.alarmDuration, .alarm_duration],
            defaultValue: 10
        )
        let hiddenMode = container.decodeFirstBool(
            forKeys: [.hiddenMode, .hidden_mode],
            defaultValue: false
        )
        let repeatEnabled = container.decodeFirstBool(
            forKeys: [.repeatEnabled, .repeat_enabled, .loopEnabled],
            defaultValue: false
        )
        let volume = container.decodeFirstFloat(
            forKeys: [.volume, .soundVolume],
            defaultValue: 0.5
        )
        let vibrationEnabled = container.decodeFirstBool(
            forKeys: [.vibrationEnabled, .vibration_enabled, .vibration],
            defaultValue: false
        )
        let useExtendedRange = try container.decodeIfPresent(Bool.self, forKey: .useExtendedRange) ?? false
        let voiceEnabled = try container.decodeIfPresent(Bool.self, forKey: .voiceEnabled) ?? true
        let repeatRounds = try container.decodeIfPresent(Int.self, forKey: .repeatRounds) ?? 0

        let soundType = container.decodeFirstSoundType(
            forKeys: [.soundType, .sound_type, .alarmSound, .sound],
            defaultValue: .intense
        )

        let clampedMin = min(max(0, rawMin), TimerConfig.maxSecondsPro)
        let cappedMax = min(rawMax, TimerConfig.maxSecondsPro)
        let clampedMax = max(clampedMin, cappedMax)
        let clampedAlarm = max(1, rawAlarm)
        let clampedVolume = min(max(volume, 0), 1)
        let clampedRounds = max(0, repeatRounds)

        self.init(
            minSeconds: clampedMin,
            maxSeconds: clampedMax,
            alarmDuration: clampedAlarm,
            hiddenMode: hiddenMode,
            repeatEnabled: repeatEnabled,
            soundType: soundType,
            volume: clampedVolume,
            vibrationEnabled: vibrationEnabled,
            useExtendedRange: useExtendedRange,
            voiceEnabled: voiceEnabled,
            repeatRounds: clampedRounds
        )
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: EncodingKeys.self)
        try container.encode(minSeconds, forKey: .minSeconds)
        try container.encode(maxSeconds, forKey: .maxSeconds)
        try container.encode(alarmDuration, forKey: .alarmDuration)
        try container.encode(hiddenMode, forKey: .hiddenMode)
        try container.encode(repeatEnabled, forKey: .repeatEnabled)
        try container.encode(soundType, forKey: .soundType)
        try container.encode(volume, forKey: .volume)
        try container.encode(vibrationEnabled, forKey: .vibrationEnabled)
        try container.encode(useExtendedRange, forKey: .useExtendedRange)
        try container.encode(voiceEnabled, forKey: .voiceEnabled)
        try container.encode(repeatRounds, forKey: .repeatRounds)
    }

    /// Returns a copy of this config with values clamped to the caller's Pro entitlement.
    /// Call this at deserialization time to enforce feature gating after subscription expiry.
    public func clamped(isPro: Bool) -> TimerConfig {
        // Respect useExtendedRange toggle for Pro users. If they opted for 5m mode (false), clamp to 5m.
        let maxAllowed = (isPro && useExtendedRange) ? TimerConfig.maxSecondsPro : TimerConfig.maxSecondsFree
        let clampedMax = Swift.min(maxSeconds, maxAllowed)
        // Ensure clampedMin is never greater than clampedMax to avoid precondition failure
        let clampedMin = Swift.min(minSeconds, clampedMax)
        
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
            useExtendedRange: isPro ? useExtendedRange : false,
            voiceEnabled: voiceEnabled,
            repeatRounds: isPro ? repeatRounds : 0
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
    static let defaultMinGapSeconds = 5

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
            // Only pull min back if max hit ceiling and gap is still too small
            if adjustedMaxSeconds - adjustedMinSeconds < minGapSeconds {
                adjustedMinSeconds = Swift.max(adjustedMaxSeconds - minGapSeconds, minSecondsLimit)
            }
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

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        let rawValue = try container.decode(String.self)
        guard let status = Self(rawValue: rawValue.lowercased()) else {
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Unknown timer status: \(rawValue)"
            )
        }
        self = status
    }
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
    public var roundCount: Int

    public init(
        config: TimerConfig,
        targetDuration: TimeInterval,
        startedAt: Date = Date(),
        remainingDuration: TimeInterval? = nil,
        status: TimerStatus = .running,
        alarmTimeRemaining: TimeInterval = 0,
        alarmStartedAt: Date? = nil,
        roundCount: Int = 1
    ) {
        self.config = config
        self.targetDuration = targetDuration
        self.startedAt = startedAt
        self.remainingDuration = remainingDuration ?? targetDuration
        self.status = status
        self.alarmTimeRemaining = alarmTimeRemaining
        self.alarmStartedAt = alarmStartedAt
        self.roundCount = roundCount
    }

    fileprivate enum DecodingKeys: String, CodingKey {
        case config
        case targetDuration
        case startedAt
        case remainingDuration
        case status
        case alarmTimeRemaining
        case alarmStartedAt
        case roundCount

        // Legacy / compatibility keys
        case target_duration
        case started_at
        case remaining_duration
        case timerStatus
        case alarm_time_remaining
        case alarm_started_at
    }

    private enum EncodingKeys: String, CodingKey {
        case config
        case targetDuration
        case startedAt
        case remainingDuration
        case status
        case alarmTimeRemaining
        case alarmStartedAt
        case roundCount
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: DecodingKeys.self)

        let config = container.decodeFirstConfig(
            forKeys: [.config],
            defaultValue: .default
        )
        let targetDuration = container.decodeFirstTimeInterval(
            forKeys: [.targetDuration, .target_duration],
            defaultValue: max(TimeInterval(config.maxSeconds), 1)
        )
        let startedAt = container.decodeFirstDate(
            forKeys: [.startedAt, .started_at],
            defaultValue: Date()
        )
        let remainingDuration = container.decodeFirstTimeInterval(
            forKeys: [.remainingDuration, .remaining_duration],
            defaultValue: targetDuration
        )
        let status = container.decodeFirstTimerStatus(
            forKeys: [.status, .timerStatus],
            defaultValue: .running
        )
        let alarmTimeRemaining = container.decodeFirstTimeInterval(
            forKeys: [.alarmTimeRemaining, .alarm_time_remaining],
            defaultValue: 0
        )
        let alarmStartedAt = container.decodeFirstDateOptional(
            forKeys: [.alarmStartedAt, .alarm_started_at]
        )
        let roundCount = try container.decodeIfPresent(Int.self, forKey: .roundCount) ?? 1

        self.init(
            config: config,
            targetDuration: max(targetDuration, 1),
            startedAt: startedAt,
            remainingDuration: max(remainingDuration, 0),
            status: status,
            alarmTimeRemaining: max(alarmTimeRemaining, 0),
            alarmStartedAt: alarmStartedAt,
            roundCount: roundCount
        )
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: EncodingKeys.self)
        try container.encode(config, forKey: .config)
        try container.encode(targetDuration, forKey: .targetDuration)
        try container.encode(startedAt, forKey: .startedAt)
        try container.encode(remainingDuration, forKey: .remainingDuration)
        try container.encode(status, forKey: .status)
        try container.encode(alarmTimeRemaining, forKey: .alarmTimeRemaining)
        try container.encodeIfPresent(alarmStartedAt, forKey: .alarmStartedAt)
        try container.encode(roundCount, forKey: .roundCount)
    }

    public var progress: Double {
        guard targetDuration > 0 else { return 0 }
        return 1.0 - (remainingDuration / targetDuration)
    }

    /// Decorative progress for the UI that doesn't reveal the true random duration.
    /// It fills based on maxSeconds, so it moves predictably but doesn't hit 100%
    /// exactly when the timer completes (unless the random duration happens to be maxSeconds).
    public var unpredictableProgress: Double {
        let elapsed = Date().timeIntervalSince(startedAt)
        let maxDuration = Double(config.maxSeconds)
        guard maxDuration > 0 else { return 0 }
        return min(0.98, elapsed / maxDuration)
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

    public init(
        timerName: String = "Random Tactical Timer",
        endDate: Date,
        minSeconds: Int = 30,
        maxSeconds: Int = 120
    ) {
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

// MARK: - Decoding Helpers

private extension KeyedDecodingContainer {
    func decodeFirstString(forKeys keys: [Key]) -> String? {
        for key in keys {
            if let value = try? decodeIfPresent(String.self, forKey: key) {
                return value
            }
        }
        return nil
    }

    func decodeFirstInt(forKeys keys: [Key], defaultValue: Int) -> Int {
        for key in keys {
            if let value = try? decodeIfPresent(Int.self, forKey: key) {
                return value
            }
            if let value = try? decodeIfPresent(Double.self, forKey: key) {
                return Int(value)
            }
            if let value = decodeFirstString(forKeys: [key]), let parsed = Int(value) {
                return parsed
            }
        }
        return defaultValue
    }

    func decodeFirstFloat(forKeys keys: [Key], defaultValue: Float) -> Float {
        for key in keys {
            if let value = try? decodeIfPresent(Float.self, forKey: key) {
                return value
            }
            if let value = try? decodeIfPresent(Double.self, forKey: key) {
                return Float(value)
            }
            if let value = decodeFirstString(forKeys: [key]), let parsed = Float(value) {
                return parsed
            }
        }
        return defaultValue
    }

    func decodeFirstBool(forKeys keys: [Key], defaultValue: Bool) -> Bool {
        for key in keys {
            if let value = try? decodeIfPresent(Bool.self, forKey: key) {
                return value
            }
            if let value = decodeFirstString(forKeys: [key]) {
                let normalized = value.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
                if ["true", "1", "yes"].contains(normalized) { return true }
                if ["false", "0", "no"].contains(normalized) { return false }
            }
            if let value = try? decodeIfPresent(Int.self, forKey: key) {
                return value != 0
            }
        }
        return defaultValue
    }

    func decodeFirstTimeInterval(forKeys keys: [Key], defaultValue: TimeInterval) -> TimeInterval {
        for key in keys {
            if let value = try? decodeIfPresent(TimeInterval.self, forKey: key) {
                return value
            }
            if let value = try? decodeIfPresent(Int.self, forKey: key) {
                return TimeInterval(value)
            }
            if let value = decodeFirstString(forKeys: [key]), let parsed = Double(value) {
                return parsed
            }
        }
        return defaultValue
    }

    func decodeFirstDate(forKeys keys: [Key], defaultValue: Date) -> Date {
        for key in keys {
            if let value = try? decodeIfPresent(Date.self, forKey: key) {
                return value
            }
            if let value = try? decodeIfPresent(TimeInterval.self, forKey: key) {
                return Date(timeIntervalSince1970: value)
            }
            if let value = decodeFirstString(forKeys: [key]) {
                if let date = ISO8601DateFormatter().date(from: value) {
                    return date
                }
                if let seconds = Double(value) {
                    return Date(timeIntervalSince1970: seconds)
                }
            }
        }
        return defaultValue
    }

    func decodeFirstDateOptional(forKeys keys: [Key]) -> Date? {
        for key in keys {
            if let value = try? decodeIfPresent(Date.self, forKey: key) {
                return value
            }
            if let value = try? decodeIfPresent(TimeInterval.self, forKey: key) {
                return Date(timeIntervalSince1970: value)
            }
            if let value = decodeFirstString(forKeys: [key]) {
                if let date = ISO8601DateFormatter().date(from: value) {
                    return date
                }
                if let seconds = Double(value) {
                    return Date(timeIntervalSince1970: seconds)
                }
            }
        }
        return nil
    }
}

private extension KeyedDecodingContainer where Key == TimerConfig.DecodingKeys {
    func decodeFirstSoundType(forKeys keys: [Key], defaultValue: SoundType) -> SoundType {
        for key in keys {
            if let value = try? decodeIfPresent(SoundType.self, forKey: key) {
                return value
            }
            if let rawValue = decodeFirstString(forKeys: [key]),
               let value = SoundType.fromLoose(rawValue) {
                return value
            }
        }
        return defaultValue
    }
}

private extension KeyedDecodingContainer where Key == TimerState.DecodingKeys {
    func decodeFirstConfig(forKeys keys: [Key], defaultValue: TimerConfig) -> TimerConfig {
        for key in keys {
            if let value = try? decodeIfPresent(TimerConfig.self, forKey: key) {
                return value
            }
        }
        return defaultValue
    }

    func decodeFirstTimerStatus(forKeys keys: [Key], defaultValue: TimerStatus) -> TimerStatus {
        for key in keys {
            if let value = try? decodeIfPresent(TimerStatus.self, forKey: key) {
                return value
            }
            if let rawValue = decodeFirstString(forKeys: [key]),
               let value = TimerStatus(rawValue: rawValue.lowercased()) {
                return value
            }
        }
        return defaultValue
    }
}
