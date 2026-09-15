import Foundation

/// Prompt + routing helpers for Apple Foundation Models / future PCC.
/// Keeps string logic testable without requiring Apple Intelligence at runtime.
enum AppleIntelligenceCoach {
    enum Backend: String, Equatable {
        case onDevice
        case privateCloudCompute
        case staticFallback
    }

    struct SessionContext: Equatable {
        let totalSessions: Int
        let currentStreak: Int
        let lastDurationSeconds: Int?
    }

    struct Tip: Equatable {
        let text: String
        let backend: Backend
    }

    static let instructions = """
        You are a concise tactical training coach for Random Tactical Timer.
        Reply with ONE short coaching tip (max 18 words). No quotes, no emoji, no preamble.
        Push the athlete toward another focused rep today — qualified training over vanity volume.
        """

    static func prompt(for context: SessionContext) -> String {
        let duration = context.lastDurationSeconds.map(String.init) ?? "unknown"
        return """
            Sessions completed lifetime: \(context.totalSessions).
            Current day streak: \(context.currentStreak).
            Last timer duration seconds: \(duration).
            Write the next-session tip.
            """
    }

    static func fallbackTip(for context: SessionContext) -> Tip {
        if context.currentStreak <= 0 {
            return Tip(
                text: "Start a short focused rep now — three completions this week unlocks real training.",
                backend: .staticFallback
            )
        }
        if context.currentStreak < 3 {
            return Tip(
                text: "Protect the streak: one more disciplined timer today keeps tomorrow easy.",
                backend: .staticFallback
            )
        }
        return Tip(
            text: "Streak strong — stack another clean rep before the day ends.",
            backend: .staticFallback
        )
    }

    /// Prefer PCC when eligible (iOS 27+ / entitlement), else on-device FM, else static.
    static func preferredBackend(
        pccRuntimeAvailable: Bool,
        onDeviceRuntimeAvailable: Bool
    ) -> Backend {
        if pccRuntimeAvailable {
            return .privateCloudCompute
        }
        if onDeviceRuntimeAvailable {
            return .onDevice
        }
        return .staticFallback
    }

    static func sanitizeModelOutput(_ raw: String) -> String {
        let trimmed = raw
            .replacingOccurrences(of: "\"", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            return fallbackTip(for: SessionContext(totalSessions: 0, currentStreak: 0, lastDurationSeconds: nil)).text
        }
        let words = trimmed.split(whereSeparator: { $0.isWhitespace })
        if words.count <= 22 {
            return trimmed
        }
        return words.prefix(18).joined(separator: " ")
    }
}
