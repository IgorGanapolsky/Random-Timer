import Foundation
#if canImport(PostHog)
import PostHog
#endif

/// Builds PostHog iOS SDK config shared by `AnalyticsService` (parity with Android `PostHogAnalyticsConfigFactory`).
enum PostHogAnalyticsConfigFactory {
    private static let posthogHost = "https://us.i.posthog.com"

#if canImport(PostHog)
    static func make(apiKey: String, isInternalUser: Bool) -> PostHogConfig {
        let config = PostHogConfig(apiKey: apiKey, host: posthogHost)
        config.captureApplicationLifecycleEvents = false
        config.captureScreenViews = false
        config.errorTrackingConfig.autoCapture = !isInternalUser
        if !isInternalUser {
            config.sessionReplay = true
            config.sessionReplayConfig.maskAllTextInputs = true
            config.sessionReplayConfig.maskAllImages = true
            config.sessionReplayConfig.captureLogs = true
            config.sessionReplayConfig.captureNetworkTelemetry = true
            config.sessionReplayConfig.screenshotMode = true
            config.sessionReplayConfig.throttleDelay = 1.0
        }
        return config
    }
#endif
}
