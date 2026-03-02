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
        guard let data = defaults.value.data(forKey: Keys.config) else {
            return nil
        }
        return decodeOrClear(TimerConfig.self, from: data, key: Keys.config, decoder: decoder)
    }

    /// Synchronous config load for use in initializers (avoids async race condition)
    nonisolated func loadConfigSync() -> TimerConfig? {
        let defaults = self.defaults
        guard let data = defaults.value.data(forKey: Keys.config) else {
            return nil
        }
        return decodeOrClear(TimerConfig.self, from: data, key: Keys.config, decoder: JSONDecoder())
    }

    // MARK: - Timer State

    func saveTimerState(_ state: TimerState) {
        guard let data = try? encoder.encode(state) else { return }
        defaults.value.set(data, forKey: Keys.timerState)
    }

    func loadTimerState() -> TimerState? {
        guard let data = defaults.value.data(forKey: Keys.timerState) else {
            return nil
        }
        return decodeOrClear(TimerState.self, from: data, key: Keys.timerState, decoder: decoder)
    }

    func clearTimerState() {
        defaults.value.removeObject(forKey: Keys.timerState)
    }

    /// Synchronous timer state load for use in initializers
    nonisolated func loadTimerStateSync() -> TimerState? {
        let defaults = self.defaults
        guard let data = defaults.value.data(forKey: Keys.timerState) else {
            return nil
        }
        return decodeOrClear(TimerState.self, from: data, key: Keys.timerState, decoder: JSONDecoder())
    }

    /// Synchronous clear for use in initializers
    nonisolated func clearTimerStateSync() {
        defaults.value.removeObject(forKey: Keys.timerState)
    }

    private nonisolated func decodeOrClear<T: Decodable>(
        _ type: T.Type,
        from data: Data,
        key: String,
        decoder: JSONDecoder
    ) -> T? {
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            defaults.value.removeObject(forKey: key)
            return nil
        }
    }
}
