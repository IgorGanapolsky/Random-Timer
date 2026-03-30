import Foundation
import os
#if canImport(PostHog)
import PostHog
#endif
#if canImport(AdServices)
import AdServices
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
    private let hasTrackedApplicationInstalledKey = "has_tracked_application_installed"
    private let utmKeys = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]
    private let appleAdsAttributionFetchedKey = "apple_ads_attribution_fetched"

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
            "is_internal": isInternalUser,
        ]
    }

    private var isInternalUser: Bool {
        // Exclude: debug builds, simulators, Maestro/UI test sessions
        #if DEBUG
        return true
        #elseif targetEnvironment(simulator)
        return true
        #else
        return ProcessInfo.processInfo.arguments.contains("-ui-test-state")
        #endif
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
        // Emit lifecycle events manually so every event includes our live/dev context tags.
        config.captureApplicationLifecycleEvents = false
        config.captureScreenViews = false
        PostHogSDK.shared.setup(config)
#endif
        initialized = true
        let distinctId = getOrCreateDistinctId()
        identify(userId: distinctId, properties: analyticsContextProperties)
        trackApplicationLifecycleEvents()
        logger.info("PostHog initialized")

        trackFirstOpenIfNeeded()
        fetchAppleSearchAdsAttribution()
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

    // MARK: - Apple Search Ads Attribution

    func fetchAppleSearchAdsAttribution() {
        guard initialized else { return }
        guard !UserDefaults.standard.bool(forKey: appleAdsAttributionFetchedKey) else { return }

#if canImport(AdServices)
        if #available(iOS 14.3, *) {
            guard let token = try? AAAttribution.attributionToken() else {
                logger.debug("No Apple Ads attribution token available")
                return
            }

            var request = URLRequest(url: URL(string: "https://api-adservices.apple.com/api/v1/")!)
            request.httpMethod = "POST"
            request.setValue("text/plain", forHTTPHeaderField: "Content-Type")
            request.httpBody = Data(token.utf8)

            URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
                guard let data = data, error == nil else {
                    self?.logger.error("Apple Ads attribution request failed: \(error?.localizedDescription ?? "unknown")")
                    return
                }

                guard let result = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                    self?.logger.error("Apple Ads attribution response not parseable")
                    return
                }

                let campaignId = result["campaignId"] as? Int ?? 0
                // campaignId 1234567890 is Apple's test/organic value — skip it
                guard campaignId != 0, campaignId != 1234567890 else {
                    self?.logger.info("Apple Ads attribution: organic install (no paid campaign)")
                    DispatchQueue.main.async {
                        guard let key = self?.appleAdsAttributionFetchedKey else { return }
                        UserDefaults.standard.set(true, forKey: key)
                    }
                    return
                }

                let attribution: [String: Any] = [
                    "utm_source": "apple_search_ads",
                    "utm_medium": "asa",
                    "utm_campaign": result["campaignName"] as? String ?? "unknown",
                    "apple_ads_campaign_id": campaignId,
                    "apple_ads_adgroup_id": result["adGroupId"] as? Int ?? 0,
                    "apple_ads_keyword": result["keyword"] as? String ?? "",
                ]

                DispatchQueue.main.async { [weak self] in
                    guard let self else { return }
                    UserDefaults.standard.set(true, forKey: self.appleAdsAttributionFetchedKey)

                    // Persist UTM params for future events
                    UserDefaults.standard.set("apple_search_ads", forKey: "utm_source")
                    UserDefaults.standard.set("asa", forKey: "utm_medium")
                    UserDefaults.standard.set(attribution["utm_campaign"], forKey: "utm_campaign")

#if canImport(PostHog)
                    PostHogSDK.shared.identify(
                        PostHogSDK.shared.getDistinctId(),
                        userProperties: attribution
                    )
                    PostHogSDK.shared.capture(AnalyticsEvents.appleAdsAttribution, properties: attribution)
#endif
                    self.logger.info("Apple Ads attribution captured: campaign=\(attribution["utm_campaign"] as? String ?? "?")")
                }
            }.resume()
        }
#endif
    }

    // MARK: - Onboarding Funnel

    private func trackApplicationLifecycleEvents() {
        let defaults = UserDefaults.standard
        track(AnalyticsEvents.applicationOpened)
        guard !defaults.bool(forKey: hasTrackedApplicationInstalledKey) else { return }
        track(AnalyticsEvents.applicationInstalled)
        defaults.set(true, forKey: hasTrackedApplicationInstalledKey)
    }

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
    static let applicationInstalled = "Application Installed"
    static let applicationOpened = "Application Opened"
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
    static let paywallPurchaseAttempt = "paywall_purchase_attempt"
    static let paywallPurchaseSuccess = "paywall_purchase_success"
    static let paywallPurchaseResult = "paywall_purchase_result"
    static let paywallRestoreResult = "paywall_restore_result"

    // Attribution
    static let deepLinkOpened = "deep_link_opened"
    static let appleAdsAttribution = "apple_ads_attribution"

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
    static let productId = "product_id"
    static let entitlementLevel = "entitlement_level"
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
