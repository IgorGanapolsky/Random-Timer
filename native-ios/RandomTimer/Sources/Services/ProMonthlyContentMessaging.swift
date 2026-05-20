import Foundation

/// User-facing copy for monthly Pro audio drop reminders.
enum ProMonthlyContentMessaging {
    struct Copy: Equatable {
        let title: String
        let body: String
    }

    static func monthLabel(releaseMonth: String) -> String {
        let trimmed = releaseMonth.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            return fallbackMonthLabel()
        }

        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy-MM"
        guard let date = formatter.date(from: trimmed) else {
            return fallbackMonthLabel()
        }

        let display = DateFormatter()
        display.locale = Locale(identifier: "en_US")
        display.dateFormat = "MMMM yyyy"
        return display.string(from: date)
    }

    static func notificationCopy(releaseMonth: String) -> Copy {
        let label = monthLabel(releaseMonth: releaseMonth)
        return Copy(
            title: "New Audio Drops for \(label)",
            body: "Your Sound Arsenal has new tactical callouts. Open the app to train with the latest pack."
        )
    }

    private static func fallbackMonthLabel() -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US")
        formatter.dateFormat = "MMMM yyyy"
        return formatter.string(from: Date())
    }
}
