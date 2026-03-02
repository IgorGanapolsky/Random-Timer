import Foundation
import os
#if canImport(PostHog)
import PostHog
#endif
#if canImport(AdServices)
import AdServices
#endif

/// Analytics Service for PostHog integration
@MainActor
final class AnalyticsService: AnalyticsHandling {
    static let shared = AnalyticsService()
    private let logger = Logger(subsystem: Bundle.main.bundleIdentifier ?? "RandomTimer", category: "Analytics")

    private var initialized = false
    private let distinctIdDefaultsKey = "posthog_distinct_id"
    private let hasFirstOpenedKey = "has_first_opened"
    private let hasFirstConfiguredKey = "has_first_configured"
    private let hasFirstCompletedKey = "has_first_completed"
    private let appleAdsAttributionFetchedKey = "apple_ads_attribution_fetched"

    private var apiKey: String { Bundle.main.object(forInfoDictionaryKey: "POSTHOG_API_KEY") as? String ?? "" }
    private var appVersion: String { Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "unknown" }
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

    private var environment: String { buildAudience == "live" ? "production" : "development" }
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
        fetchAppleSearchAdsAttribution()
    }

    func event(_ name: String, properties: [String: Any]? = nil) {
        let payload = mergedProperties(properties)
#if DEBUG
        testEventHandler?(name, payload)
#endif
        guard initialized else { return }
#if canImport(PostHog)
        PostHogSDK.shared.capture(name, properties: payload)
#endif
    }

    func track(_ name: String, properties: [String: Any]? = nil) {
        event(name, properties: properties)
    }

    func screen(_ name: String) {
        guard initialized else { return }
#if canImport(PostHog)
        PostHogSDK.shared.screen(name, properties: analyticsContextProperties)
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

    func fetchAppleSearchAdsAttribution() {
        guard initialized else { return }
        let defaults = UserDefaults.standard
        guard !defaults.bool(forKey: appleAdsAttributionFetchedKey) else { return }

#if canImport(AdServices)
        if #available(iOS 14.3, *) {
            guard let token = try? AAAttribution.attributionToken() else { return }
            var request = URLRequest(url: URL(string: "https://api-adservices.apple.com/api/v1/")!)
            request.httpMethod = "POST"
            request.setValue("text/plain", forHTTPHeaderField: "Content-Type")
            request.httpBody = Data(token.utf8)

            URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
                guard let data = data, error == nil else { return }
                guard let result = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }
                let campaignId = result["campaignId"] as? Int ?? 0
                guard campaignId != 0, campaignId != 1234567890 else {
                    DispatchQueue.main.async { defaults.set(true, forKey: self?.appleAdsAttributionFetchedKey ?? "") }
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
                    defaults.set(true, forKey: self?.appleAdsAttributionFetchedKey ?? "")
                    defaults.set("apple_search_ads", forKey: "utm_source")
                    defaults.set("asa", forKey: "utm_medium")
                    defaults.set(attribution["utm_campaign"] ?? "unknown", forKey: "utm_campaign")
#if canImport(PostHog)
                    PostHogSDK.shared.identify(PostHogSDK.shared.getDistinctId(), userProperties: attribution)
                    PostHogSDK.shared.capture(AnalyticsEvents.appleAdsAttribution, properties: attribution)
#endif
                }
            }.resume()
        }
#endif
    }

    private func trackFirstOpenIfNeeded() {
        let defaults = UserDefaults.standard
        guard !defaults.bool(forKey: hasFirstOpenedKey) else { return }
        event(AnalyticsEvents.firstOpen)
        defaults.set(true, forKey: hasFirstOpenedKey)
    }

    func trackFirstTimerConfiguredIfNeeded() {
        guard initialized else { return }
        let defaults = UserDefaults.standard
        guard !defaults.bool(forKey: hasFirstConfiguredKey) else { return }
        event(AnalyticsEvents.firstTimerConfigured)
        defaults.set(true, forKey: hasFirstConfiguredKey)
    }

    func trackFirstTimerCompletedIfNeeded() {
        guard initialized else { return }
        let defaults = UserDefaults.standard
        guard !defaults.bool(forKey: hasFirstCompletedKey) else { return }
        event(AnalyticsEvents.firstTimerCompleted)
        defaults.set(true, forKey: hasFirstCompletedKey)
    }

    private func getOrCreateDistinctId() -> String {
        let defaults = UserDefaults.standard
        if let existing = defaults.string(forKey: distinctIdDefaultsKey), !existing.isEmpty { return existing }
        let generated = UUID().uuidString
        defaults.set(generated, forKey: distinctIdDefaultsKey)
        return generated
    }
}

enum AnalyticsEvents {
    static let firstOpen = "first_open"
    static let firstTimerConfigured = "first_timer_configured"
    static let firstTimerCompleted = "first_timer_completed"
    static let appleAdsAttribution = "apple_ads_attribution"
    static let reviewPromptRequested = "review_prompt_requested"
    static let writeReviewTapped = "write_review_tapped"
}

enum AnalyticsProperties {
    static let environment = "environment"
    static let buildAudience = "build_audience"
    static let buildType = "build_type"
    static let runtimeTarget = "runtime_target"
}
