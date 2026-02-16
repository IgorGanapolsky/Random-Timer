import Foundation

/// Thread-safe wrapper for UserDefaults to satisfy Swift 6 Sendable requirements
private struct SendableDefaults: @unchecked Sendable {
    let value: UserDefaults
}

/// Service for persisting timer configuration and state
actor StorageService: TimerStorage {

    private let defaults: SendableDefaults
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    init(defaults: UserDefaults = .standard) {
        self.defaults = SendableDefaults(value: defaults)
    }

    // MARK: - Keys

    private enum Keys {
        static let config = "timer_config"
        static let timerState = "active_timer_state"
    }

    // MARK: - Config

    func saveConfig(_ config: TimerConfig) {
        guard let data = try? encoder.encode(config) else { return }
        defaults.value.set(data, forKey: Keys.config)
    }

    func loadConfig() -> TimerConfig? {
        guard let data = defaults.value.data(forKey: Keys.config),
              let config = try? decoder.decode(TimerConfig.self, from: data) else {
            return nil
        }
        return config
    }

    /// Synchronous config load for use in initializers (avoids async race condition)
    nonisolated func loadConfigSync() -> TimerConfig? {
        let defaults = self.defaults
        guard let data = defaults.value.data(forKey: Keys.config),
              let config = try? JSONDecoder().decode(TimerConfig.self, from: data) else {
            return nil
        }
        return config
    }

    // MARK: - Timer State

    func saveTimerState(_ state: TimerState) {
        guard let data = try? encoder.encode(state) else { return }
        defaults.value.set(data, forKey: Keys.timerState)
    }

    func loadTimerState() -> TimerState? {
        guard let data = defaults.value.data(forKey: Keys.timerState),
              let state = try? decoder.decode(TimerState.self, from: data) else {
            return nil
        }
        return state
    }

    func clearTimerState() {
        defaults.value.removeObject(forKey: Keys.timerState)
    }

    /// Synchronous timer state load for use in initializers
    nonisolated func loadTimerStateSync() -> TimerState? {
        let defaults = self.defaults
        guard let data = defaults.value.data(forKey: Keys.timerState),
              let state = try? JSONDecoder().decode(TimerState.self, from: data) else {
            return nil
        }
        return state
    }

    /// Synchronous clear for use in initializers
    nonisolated func clearTimerStateSync() {
        defaults.value.removeObject(forKey: Keys.timerState)
    }
}
