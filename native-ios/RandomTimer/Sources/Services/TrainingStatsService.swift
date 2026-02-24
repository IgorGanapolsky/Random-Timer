import Foundation

/// Tracks training session count and consecutive-day streaks using UserDefaults.
@MainActor
final class TrainingStatsService {
    static let shared = TrainingStatsService()

    private let defaults = UserDefaults.standard
    private let totalSessionsKey = "training_total_sessions"
    private let lastTrainingDateKey = "training_last_date"
    private let streakKey = "training_streak"

    var totalSessions: Int { defaults.integer(forKey: totalSessionsKey) }
    var currentStreak: Int { defaults.integer(forKey: streakKey) }

    private init() {}

    func recordSession() {
        // Increment total
        let total = totalSessions + 1
        defaults.set(total, forKey: totalSessionsKey)

        // Update streak
        let today = Calendar.current.startOfDay(for: Date())
        let lastDate = defaults.object(forKey: lastTrainingDateKey) as? Date
        let lastDay = lastDate.map { Calendar.current.startOfDay(for: $0) }

        if let lastDay = lastDay {
            let daysBetween = Calendar.current.dateComponents([.day], from: lastDay, to: today).day ?? 0
            if daysBetween == 1 {
                // Consecutive day -- increment streak
                defaults.set(currentStreak + 1, forKey: streakKey)
            } else if daysBetween > 1 {
                // Streak broken -- reset to 1
                defaults.set(1, forKey: streakKey)
            }
            // daysBetween == 0 means same day, streak stays
        } else {
            // First ever session
            defaults.set(1, forKey: streakKey)
        }

        defaults.set(today, forKey: lastTrainingDateKey)
    }
}
