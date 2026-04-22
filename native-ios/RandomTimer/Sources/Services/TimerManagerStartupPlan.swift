import Foundation

struct TimerManagerStartupPlan: Equatable {
    let initialConfig: TimerConfig
    let shouldClearPersistedTimerState: Bool
    let shouldRestoreActiveTimer: Bool

    static func resolve(
        rawConfig: TimerConfig?,
        persistedTimerState: TimerState?,
        isPro: Bool
    ) -> Self {
        let initialConfig = (rawConfig ?? .default).clamped(isPro: isPro)

        guard let persistedTimerState else {
            return Self(
                initialConfig: initialConfig,
                shouldClearPersistedTimerState: false,
                shouldRestoreActiveTimer: false
            )
        }

        switch persistedTimerState.status {
        case .alarm, .complete:
            return Self(
                initialConfig: initialConfig,
                shouldClearPersistedTimerState: true,
                shouldRestoreActiveTimer: false
            )
        default:
            return Self(
                initialConfig: initialConfig,
                shouldClearPersistedTimerState: false,
                shouldRestoreActiveTimer: true
            )
        }
    }
}
