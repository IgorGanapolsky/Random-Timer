import Foundation

/// Pure policy for hardware volume button behavior during alarm playback.
enum AlarmVolumeKeyPolicy {
    static func shouldSilenceOnVolumeChange(
        status: TimerStatus?,
        isAlarmSilenced: Bool,
        previousVolume: Float,
        newVolume: Float
    ) -> Bool {
        guard status == .alarm, !isAlarmSilenced else { return false }
        return previousVolume != newVolume
    }
}
