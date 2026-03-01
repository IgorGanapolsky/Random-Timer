import Foundation
import os

/// Local persistence using UserDefaults
actor StorageService: TimerStorage {
    private let userDefaults: UserDefaults
    private let configKey = "timer_config"
    private let stateKey = "timer_active_state"
    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "storage")

    init(userDefaults: UserDefaults = .standard) {
        self.userDefaults = userDefaults
    }

    func saveTimerConfig(_ config: TimerConfig) async {
        do {
            let data = try JSONEncoder().encode(config)
            userDefaults.set(data, forKey: configKey)
        } catch {
            Self.log.error("Failed to save config: \(error)")
        }
    }

    func getTimerConfig() async -> TimerConfig {
        guard let data = userDefaults.data(forKey: configKey) else { return .default }
        do {
            return try JSONDecoder().decode(TimerConfig.self, from: data)
        } catch {
            Self.log.error("Failed to load config: \(error)")
            return .default
        }
    }

    func saveTimerState(_ state: TimerState) async {
        do {
            let data = try JSONEncoder().encode(state)
            userDefaults.set(data, forKey: stateKey)
        } catch {
            Self.log.error("Failed to save state: \(error)")
        }
    }

    func loadTimerState() async -> TimerState? {
        guard let data = userDefaults.data(forKey: stateKey) else { return nil }
        do {
            return try JSONDecoder().decode(TimerState.self, from: data)
        } catch {
            Self.log.error("Failed to load state: \(error)")
            return nil
        }
    }

    func clearTimerState() async {
        userDefaults.removeObject(forKey: stateKey)
    }

    func saveConfig(_ config: TimerConfig) async { await saveTimerConfig(config) }
    func loadConfig() async -> TimerConfig? { await getTimerConfig() }
    
    @MainActor func loadConfigSync() -> TimerConfig? {
        guard let data = UserDefaults.standard.data(forKey: configKey) else { return nil }
        return try? JSONDecoder().decode(TimerConfig.self, from: data)
    }

    @MainActor func loadTimerStateSync() -> TimerState? {
        guard let data = UserDefaults.standard.data(forKey: stateKey) else { return nil }
        return try? JSONDecoder().decode(TimerState.self, from: data)
    }

    @MainActor func clearTimerStateSync() {
        UserDefaults.standard.removeObject(forKey: stateKey)
    }
}
