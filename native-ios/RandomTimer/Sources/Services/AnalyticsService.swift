import Foundation
import PostHog

/// Analytics Service for PostHog integration
@MainActor
final class AnalyticsService {
    static let shared = AnalyticsService()

    private var initialized = false

    private let apiKey = "phc_cpuhUFoXKeG15GoZBwwEZJToeRX07FRZI4Ty0WCW2da"
    private let host = "https://us.i.posthog.com"

    private init() {}

    func initialize() {
        guard !initialized else { return }
        guard !apiKey.isEmpty else {
            print("[Analytics] No API key configured - analytics disabled")
            return
        }

        let config = PostHogConfig(apiKey: apiKey, host: host)
        config.captureApplicationLifecycleEvents = true
        config.captureScreenViews = false // We track manually
        PostHogSDK.shared.setup(config)
        initialized = true
        print("[Analytics] PostHog initialized")
    }

    func track(_ event: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
        PostHogSDK.shared.capture(event, properties: properties)
    }

    func screen(_ screenName: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
        PostHogSDK.shared.screen(screenName, properties: properties)
    }

    func identify(userId: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
        PostHogSDK.shared.identify(userId, userProperties: properties)
    }

    func reset() {
        guard initialized else { return }
        PostHogSDK.shared.reset()
    }

    func flush() {
        guard initialized else { return }
        PostHogSDK.shared.flush()
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
