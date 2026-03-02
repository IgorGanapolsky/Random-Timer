import SwiftUI

/// Timer app color palette - high-intensity tactical red
extension Color {

    // MARK: - Background Colors

    static let backgroundDark = Color(hex: "0A0A0F")
    static let backgroundLight = Color(hex: "141419")

    // MARK: - Timer State Colors

    static let timerActive = Color(hex: "10B981")      // Emerald green - running
    static let timerWarning = Color(hex: "F59E0B")     // Amber - < 30 seconds
    static let timerDanger = Color(hex: "EF4444")      // Tactical red - < 10 seconds
    static let timerComplete = Color(hex: "DC2626")    // Crimson red - complete/alarm

    // MARK: - Glassmorphism

    static let glassBackground = Color.white.opacity(0.10)
    static let glassBorder = Color.white.opacity(0.20)
    static let glassHighlight = Color.white.opacity(0.30)

    // MARK: - Text Colors

    static let textPrimary = Color(hex: "F8FAFC")      // Near white
    static let textSecondary = Color(hex: "A1A1AA")    // Muted gray
    static let textMuted = Color(hex: "71717A")        // Dim gray

    // MARK: - Accent Colors

    static let accentPrimary = Color(hex: "DC2626")    // Crimson red (matches Android)
    static let accentSecondary = Color(hex: "EF4444")  // Bright red

    // MARK: - Helper

    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - Timer Status Color Extension

extension TimerStatus {
    var color: Color {
        switch self {
        case .idle:
            return .textSecondary
        case .running:
            return .timerActive
        case .warning, .danger:
            return .timerWarning
        case .complete, .alarm:
            return .timerComplete
        case .paused:
            return .textSecondary
        }
    }
}
