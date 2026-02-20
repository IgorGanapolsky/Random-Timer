package com.iganapolsky.randomtimer.analytics

import android.app.Application
import com.iganapolsky.randomtimer.BuildConfig
import com.posthog.PostHog
import com.posthog.android.PostHogAndroid
import com.posthog.android.PostHogAndroidConfig
import javax.inject.Inject
import javax.inject.Singleton
import java.util.UUID

@Singleton
class AnalyticsService @Inject constructor() {

    private var initialized = false

    fun initialize(application: Application) {
        if (initialized) return

        val apiKey = BuildConfig.POSTHOG_API_KEY
        if (apiKey.isBlank()) {
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
        identify(
            userId = getOrCreateDistinctId(application),
            properties = mapOf(
                "platform" to "android",
                "app_version" to BuildConfig.VERSION_NAME,
            ),
        )
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

    private fun getOrCreateDistinctId(application: Application): String {
        val prefs = application.getSharedPreferences(PREFS_NAME, Application.MODE_PRIVATE)
        val existing = prefs.getString(KEY_DISTINCT_ID, null)
        if (!existing.isNullOrBlank()) {
            return existing
        }
        val generated = UUID.randomUUID().toString()
        prefs.edit().putString(KEY_DISTINCT_ID, generated).apply()
        return generated
    }

    companion object {
        private const val PREFS_NAME = "random_timer_analytics"
        private const val KEY_DISTINCT_ID = "posthog_distinct_id"
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
    const val REVIEW_PROMPT_REQUESTED = "review_prompt_requested"
    const val WRITE_REVIEW_TAPPED = "write_review_tapped"
}

object AnalyticsScreens {
    const val TIMER_SETUP = "Timer Setup"
    const val ACTIVE_TIMER = "Active Timer"
}
