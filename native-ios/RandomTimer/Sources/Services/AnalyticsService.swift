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
    private let distinctIdDefaultsKey = "posthog_distinct_id"
    private let hasFirstOpenedKey = "has_first_opened"
    private let hasFirstConfiguredKey = "has_first_configured"
    private let hasFirstCompletedKey = "has_first_completed"
    private let utmKeys = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]

    // API key loaded from Info.plist (set POSTHOG_API_KEY in build settings)
    private var apiKey: String {
        Bundle.main.object(forInfoDictionaryKey: "POSTHOG_API_KEY") as? String ?? ""
    }
    private var appVersion: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "unknown"
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
        let distinctId = getOrCreateDistinctId()
        
        #if DEBUG
        let environment = "development"
        #else
        let environment = "production"
        #endif
        
        identify(userId: distinctId, properties: [
            "platform": "ios",
            "app_version": appVersion,
            "environment": environment
        ])
        initialized = true
        print("[Analytics] PostHog initialized")

        trackFirstOpenIfNeeded()
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

    // MARK: - UTM Attribution

    func trackDeepLink(_ url: URL) {
        guard initialized else { return }
        let utmParams = extractUtmParams(from: url)
        guard !utmParams.isEmpty else { return }

        // Persist attribution
        let defaults = UserDefaults.standard
        for (key, value) in utmParams {
            defaults.set(value, forKey: key)
        }

        // Set as person properties for all future events
#if canImport(PostHog)
        PostHogSDK.shared.identify(
            PostHogSDK.shared.getDistinctId(),
            userProperties: utmParams
        )
#endif
        track(AnalyticsEvents.deepLinkOpened, properties: utmParams)
    }

    private func extractUtmParams(from url: URL) -> [String: Any] {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: true) else {
            return [:]
        }
        var params: [String: Any] = [:]
        for key in utmKeys {
            if let value = components.queryItems?.first(where: { $0.name == key })?.value,
               !value.isEmpty {
                params[key] = value
            }
        }
        if let path = components.path as String?, !path.isEmpty {
            params["referring_path"] = path
        }
        return params
    }

    // MARK: - Onboarding Funnel

    private func trackFirstOpenIfNeeded() {
        let defaults = UserDefaults.standard
        guard !defaults.bool(forKey: hasFirstOpenedKey) else { return }
        track(AnalyticsEvents.firstOpen)
        defaults.set(true, forKey: hasFirstOpenedKey)
    }

    func trackFirstTimerConfiguredIfNeeded() {
        guard initialized else { return }
        let defaults = UserDefaults.standard
        guard !defaults.bool(forKey: hasFirstConfiguredKey) else { return }
        track(AnalyticsEvents.firstTimerConfigured)
        defaults.set(true, forKey: hasFirstConfiguredKey)
    }

    func trackFirstTimerCompletedIfNeeded() {
        guard initialized else { return }
        let defaults = UserDefaults.standard
        guard !defaults.bool(forKey: hasFirstCompletedKey) else { return }
        track(AnalyticsEvents.firstTimerCompleted)
        defaults.set(true, forKey: hasFirstCompletedKey)
    }

    // MARK: - Stored Attribution

    func getStoredAttribution() -> [String: String] {
        let defaults = UserDefaults.standard
        var result: [String: String] = [:]
        for key in utmKeys {
            if let value = defaults.string(forKey: key) {
                result[key] = value
            }
        }
        return result
    }

    private func getOrCreateDistinctId() -> String {
        let defaults = UserDefaults.standard
        if let existing = defaults.string(forKey: distinctIdDefaultsKey),
           existing.isEmpty == false {
            return existing
        }

        let generated = UUID().uuidString
        defaults.set(generated, forKey: distinctIdDefaultsKey)
        return generated
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
    static let timerAbandoned = "timer_abandoned"
    static let timerCountdownFinished = "timer_countdown_finished"
    static let settingsChanged = "settings_changed"
    static let reviewPromptRequested = "review_prompt_requested"
    static let writeReviewTapped = "write_review_tapped"

    // UTM Attribution
    static let deepLinkOpened = "deep_link_opened"

    // Onboarding Funnel
    static let firstOpen = "first_open"
    static let firstTimerConfigured = "first_timer_configured"
    static let firstTimerCompleted = "first_timer_completed"
}

enum AnalyticsScreens {
    static let timerSetup = "Timer Setup"
    static let activeTimer = "Active Timer"
}
