import Foundation
import os
#if canImport(PostHog)
import PostHog
#endif

/// Analytics Service for PostHog integration
/// To enable: Add PostHog Swift SDK via SPM (https://github.com/PostHog/posthog-ios)
@MainActor
final class AnalyticsService {
    static let shared = AnalyticsService()
    private let logger = Logger(subsystem: Bundle.main.bundleIdentifier ?? "RandomTimer", category: "Analytics")

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

#if DEBUG
    var testEventHandler: ((_ event: String, _ properties: [String: Any]?) -> Void)?
#endif

    private init() {}

    private var analyticsContextProperties: [String: Any] {
        [
            "platform": "ios",
            "app_version": appVersion,
            AnalyticsProperties.environment: environment,
            AnalyticsProperties.buildAudience: buildAudience,
            AnalyticsProperties.buildType: buildType,
            AnalyticsProperties.runtimeTarget: runtimeTarget,
        ]
    }

    private var buildAudience: String {
#if DEBUG
        return "dev"
#else
        #if targetEnvironment(simulator)
        return "dev"
        #else
        return "live"
        #endif
#endif
    }

    private var buildType: String {
#if DEBUG
        return "debug"
#else
        return "release"
#endif
    }

    private var environment: String {
        buildAudience == "live" ? "production" : "development"
    }

    private var runtimeTarget: String {
#if targetEnvironment(simulator)
        return "simulator"
#else
        return "device"
#endif
    }

    private func mergedProperties(_ properties: [String: Any]?) -> [String: Any] {
        guard var props = properties else { return analyticsContextProperties }
        for (key, value) in analyticsContextProperties {
            props[key] = value
        }
        return props
    }

    func initialize() {
        guard !initialized else { return }
        guard !apiKey.isEmpty else {
            logger.notice("No API key configured - analytics disabled")
            return
        }

#if canImport(PostHog)
        let config = PostHogConfig(apiKey: apiKey, host: host)
        config.captureApplicationLifecycleEvents = true
        config.captureScreenViews = false
        PostHogSDK.shared.setup(config)
#endif
        initialized = true
        let distinctId = getOrCreateDistinctId()
        identify(userId: distinctId, properties: analyticsContextProperties)
        logger.info("PostHog initialized")

        trackFirstOpenIfNeeded()
    }

    func track(_ event: String, properties: [String: Any]? = nil) {
        let payload = mergedProperties(properties)
#if DEBUG
        testEventHandler?(event, payload)
#endif
        guard initialized else { return }
#if canImport(PostHog)
        PostHogSDK.shared.capture(event, properties: payload)
#endif
    }

    func screen(_ screenName: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
#if canImport(PostHog)
        PostHogSDK.shared.screen(screenName, properties: mergedProperties(properties))
#endif
    }

    func identify(userId: String, properties: [String: Any]? = nil) {
        guard initialized else { return }
#if canImport(PostHog)
        PostHogSDK.shared.identify(userId, userProperties: mergedProperties(properties))
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
    static let paywallViewed = "paywall_viewed"
    static let paywallDismissed = "paywall_dismissed"
    static let paywallPurchaseResult = "paywall_purchase_result"
    static let paywallRestoreResult = "paywall_restore_result"

    // UTM Attribution
    static let deepLinkOpened = "deep_link_opened"

    // Onboarding Funnel
    static let firstOpen = "first_open"
    static let firstTimerConfigured = "first_timer_configured"
    static let firstTimerCompleted = "first_timer_completed"
}

enum AnalyticsProperties {
    static let entryPoint = "entry_point"
    static let result = "result"
    static let abandonReason = "abandon_reason"
    static let abandonSource = "abandon_source"
    static let dismissMethod = "dismiss_method"
    static let environment = "environment"
    static let buildAudience = "build_audience"
    static let buildType = "build_type"
    static let runtimeTarget = "runtime_target"
}

enum AnalyticsValues {
    static let abandonReasonUserCancelled = "user_cancelled"
    static let abandonReasonStaleRestoreExpired = "stale_restore_expired"
    static let abandonSourceTimerControls = "timer_controls"
    static let abandonSourceStateRestore = "state_restore"
}

enum AnalyticsScreens {
    static let timerSetup = "Timer Setup"
    static let activeTimer = "Active Timer"
}
