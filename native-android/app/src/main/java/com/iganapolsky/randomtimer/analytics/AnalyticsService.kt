package com.iganapolsky.randomtimer.analytics

import android.app.Application
import com.posthog.PostHog
import com.posthog.android.PostHogAndroid
import com.posthog.android.PostHogAndroidConfig
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AnalyticsService @Inject constructor() {

    private var initialized = false

    fun initialize(application: Application) {
        if (initialized) return

        val apiKey = "phc_REPLACE_WITH_YOUR_KEY" // TODO: Replace with actual PostHog API key
        if (apiKey.startsWith("phc_REPLACE")) {
            // Skip initialization if no real API key
            return
        }

        val config = PostHogAndroidConfig(
            apiKey = apiKey,
            host = "https://us.i.posthog.com"
        ).apply {
            captureApplicationLifecycleEvents = true
            captureDeepLinks = true
            captureScreenViews = false // We track manually for better control
        }

        PostHogAndroid.setup(application, config)
        initialized = true
    }

    fun track(event: String, properties: Map<String, Any>? = null) {
        if (!initialized) return
        PostHog.capture(event, properties = properties)
    }

    fun screen(screenName: String, properties: Map<String, Any>? = null) {
        if (!initialized) return
        PostHog.screen(screenName, properties)
    }

    fun identify(userId: String, properties: Map<String, Any>? = null) {
        if (!initialized) return
        PostHog.identify(userId, properties)
    }

    fun reset() {
        if (!initialized) return
        PostHog.reset()
    }

    fun flush() {
        if (!initialized) return
        PostHog.flush()
    }
}

// Event names for consistency
object AnalyticsEvents {
    const val TIMER_STARTED = "timer_started"
    const val TIMER_COMPLETED = "timer_completed"
    const val TIMER_PAUSED = "timer_paused"
    const val TIMER_RESUMED = "timer_resumed"
    const val TIMER_RESET = "timer_reset"
    const val TIMER_STOPPED = "timer_stopped"
    const val ALARM_TRIGGERED = "alarm_triggered"
    const val ALARM_DISMISSED = "alarm_dismissed"
    const val SETTINGS_CHANGED = "settings_changed"
}

object AnalyticsScreens {
    const val TIMER_SETUP = "Timer Setup"
    const val ACTIVE_TIMER = "Active Timer"
}
