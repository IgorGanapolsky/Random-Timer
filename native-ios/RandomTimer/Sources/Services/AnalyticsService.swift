import Foundation
#if canImport(PostHog)
import PostHog
#endif

/// Analytics Service for PostHog integration
/// To enable: Add PostHog Swift SDK via SPM (https://github.com/PostHog/posthog-ios)
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

#if canImport(PostHog)
        let config = PostHogConfig(apiKey: apiKey, host: host)
        config.captureApplicationLifecycleEvents = true
        config.captureScreenViews = false
        PostHogSDK.shared.setup(config)
#endif
        initialized = true
        print("[Analytics] PostHog initialized")
    }

    func track(_ event: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
#if canImport(PostHog)
        PostHogSDK.shared.capture(event, properties: properties)
#endif
    }

    func screen(_ screenName: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
#if canImport(PostHog)
        PostHogSDK.shared.screen(screenName, properties: properties)
#endif
    }

    func identify(userId: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
#if canImport(PostHog)
        PostHogSDK.shared.identify(userId, userProperties: properties)
#endif
    }

    func reset() {
        guard initialized else { return }
#if canImport(PostHog)
        PostHogSDK.shared.reset()
#endif
    }

    func flush() {
        guard initialized else { return }
#if canImport(PostHog)
        PostHogSDK.shared.flush()
#endif
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
    static let reviewPromptRequested = "review_prompt_requested"
    static let writeReviewTapped = "write_review_tapped"
}

enum AnalyticsScreens {
    static let timerSetup = "Timer Setup"
    static let activeTimer = "Active Timer"
}
