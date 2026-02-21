package com.iganapolsky.randomtimer.analytics

import android.app.Application
import android.content.SharedPreferences
import android.net.Uri
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
    private var prefs: SharedPreferences? = null

    fun initialize(application: Application) {
        if (initialized) return

        prefs = application.getSharedPreferences(PREFS_NAME, Application.MODE_PRIVATE)

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

        trackFirstOpenIfNeeded()
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

    // --- UTM Attribution ---

    fun trackDeepLink(uri: Uri) {
        if (!initialized) return
        val utmParams = extractUtmParams(uri)
        if (utmParams.isNotEmpty()) {
            // Persist attribution for this user
            prefs?.edit()?.apply {
                utmParams.forEach { (key, value) -> putString(key, value.toString()) }
                apply()
            }
            // Set as person properties so all future events carry attribution
            PostHog.identify(
                PostHog.distinctId(),
                userProperties = utmParams,
            )
            track(AnalyticsEvents.DEEP_LINK_OPENED, utmParams)
        }
    }

    private fun extractUtmParams(uri: Uri): Map<String, Any> {
        val params = mutableMapOf<String, Any>()
        UTM_KEYS.forEach { key ->
            uri.getQueryParameter(key)?.takeIf { it.isNotBlank() }?.let {
                params[key] = it
            }
        }
        // Also capture the referring URL path for content attribution
        uri.path?.takeIf { it.isNotBlank() }?.let {
            params["referring_path"] = it
        }
        return params
    }

    // --- Onboarding Funnel ---

    private fun trackFirstOpenIfNeeded() {
        val hasOpened = prefs?.getBoolean(KEY_HAS_OPENED, false) ?: false
        if (!hasOpened) {
            track(AnalyticsEvents.FIRST_OPEN)
            prefs?.edit()?.putBoolean(KEY_HAS_OPENED, true)?.apply()
        }
    }

    fun trackFirstTimerConfiguredIfNeeded() {
        if (!initialized) return
        val hasConfigured = prefs?.getBoolean(KEY_HAS_CONFIGURED, false) ?: false
        if (!hasConfigured) {
            track(AnalyticsEvents.FIRST_TIMER_CONFIGURED)
            prefs?.edit()?.putBoolean(KEY_HAS_CONFIGURED, true)?.apply()
        }
    }

    fun trackFirstTimerCompletedIfNeeded() {
        if (!initialized) return
        val hasCompleted = prefs?.getBoolean(KEY_HAS_COMPLETED, false) ?: false
        if (!hasCompleted) {
            track(AnalyticsEvents.FIRST_TIMER_COMPLETED)
            prefs?.edit()?.putBoolean(KEY_HAS_COMPLETED, true)?.apply()
        }
    }

    // --- Stored Attribution ---

    fun getStoredAttribution(): Map<String, String> {
        val result = mutableMapOf<String, String>()
        prefs?.let { p ->
            UTM_KEYS.forEach { key ->
                p.getString(key, null)?.let { result[key] = it }
            }
        }
        return result
    }

    private fun getOrCreateDistinctId(application: Application): String {
        val existing = prefs?.getString(KEY_DISTINCT_ID, null)
        if (!existing.isNullOrBlank()) {
            return existing
        }
        val generated = UUID.randomUUID().toString()
        prefs?.edit()?.putString(KEY_DISTINCT_ID, generated)?.apply()
        return generated
    }

    companion object {
        private const val PREFS_NAME = "random_timer_analytics"
        private const val KEY_DISTINCT_ID = "posthog_distinct_id"
        private const val KEY_HAS_OPENED = "has_first_opened"
        private const val KEY_HAS_CONFIGURED = "has_first_configured"
        private const val KEY_HAS_COMPLETED = "has_first_completed"
        private val UTM_KEYS = listOf(
            "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"
        )
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

    // UTM Attribution
    const val DEEP_LINK_OPENED = "deep_link_opened"

    // Onboarding Funnel
    const val FIRST_OPEN = "first_open"
    const val FIRST_TIMER_CONFIGURED = "first_timer_configured"
    const val FIRST_TIMER_COMPLETED = "first_timer_completed"
}

object AnalyticsScreens {
    const val TIMER_SETUP = "Timer Setup"
    const val ACTIVE_TIMER = "Active Timer"
}
