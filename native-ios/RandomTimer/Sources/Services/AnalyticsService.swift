import Foundation

/// Analytics Service for PostHog integration
/// To enable: Add PostHog Swift SDK via SPM and set your API key below
@MainActor
final class AnalyticsService {
    static let shared = AnalyticsService()

    private var initialized = false

    // API key loaded from Info.plist (set POSTHOG_API_KEY in build settings)
    private var apiKey: String {
        Bundle.main.object(forInfoDictionaryKey: "POSTHOG_API_KEY") as? String ?? ""
    }
    private let host = "https://us.i.posthog.com"

    private init() {}

    func initialize() {
        guard !initialized else { return }
        guard !apiKey.isEmpty else {
            print("[Analytics] No API key configured - analytics disabled")
            return
        }

        // TODO: Initialize PostHog when SDK is added
        // PostHogSDK.shared.setup(PostHogConfig(apiKey: apiKey, host: host))
        initialized = true
        print("[Analytics] PostHog initialized")
    }

    func track(_ event: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
        // TODO: PostHogSDK.shared.capture(event, properties: properties)
        print("[Analytics] Track: \(event)")
    }

    func screen(_ screenName: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
        // TODO: PostHogSDK.shared.screen(screenName, properties: properties)
        print("[Analytics] Screen: \(screenName)")
    }

    func identify(userId: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
        // TODO: PostHogSDK.shared.identify(userId, userProperties: properties)
    }

    func reset() {
        guard initialized else { return }
        // TODO: PostHogSDK.shared.reset()
    }

    func flush() {
        guard initialized else { return }
        // TODO: PostHogSDK.shared.flush()
    }
}

// Event names for consistency
enum AnalyticsEvents {
    static let timerStarted = "timer_started"
    static let timerCompleted = "timer_completed"
    static let timerPaused = "timer_paused"
    static let timerResumed = "timer_resumed"
    static let timerReset = "timer_reset"
    static let timerStopped = "timer_stopped"
    static let alarmTriggered = "alarm_triggered"
    static let alarmDismissed = "alarm_dismissed"
    static let settingsChanged = "settings_changed"
}

enum AnalyticsScreens {
    static let timerSetup = "Timer Setup"
    static let activeTimer = "Active Timer"
}
