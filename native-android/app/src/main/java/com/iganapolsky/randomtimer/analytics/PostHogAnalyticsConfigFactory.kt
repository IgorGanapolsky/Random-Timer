package com.iganapolsky.randomtimer.analytics

import com.posthog.android.PostHogAndroidConfig

/** Builds PostHog Android SDK config shared by [AnalyticsService]. */
object PostHogAnalyticsConfigFactory {
    private const val POSTHOG_HOST = "https://us.i.posthog.com"

    fun create(
        apiKey: String,
        isInternalUser: Boolean,
    ): PostHogAndroidConfig =
        PostHogAndroidConfig(
            apiKey = apiKey,
            host = POSTHOG_HOST,
        ).apply {
            captureApplicationLifecycleEvents = false
            captureDeepLinks = true
            captureScreenViews = false
            preloadFeatureFlags = true
            errorTrackingConfig.autoCapture = !isInternalUser
            if (!isInternalUser) {
                sessionReplay = true
                sessionReplayConfig.maskAllTextInputs = true
                sessionReplayConfig.maskAllImages = true
                sessionReplayConfig.captureLogcat = true
                sessionReplayConfig.screenshot = true
                sessionReplayConfig.debouncerDelayMs = 1000L
            }
        }
}
