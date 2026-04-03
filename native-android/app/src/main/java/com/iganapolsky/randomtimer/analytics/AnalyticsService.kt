package com.iganapolsky.randomtimer.analytics

import android.app.Application
import android.content.SharedPreferences
import android.net.Uri
import android.os.Build
import com.iganapolsky.randomtimer.BuildConfig
import com.posthog.PostHog
import com.posthog.android.PostHogAndroid
import com.posthog.android.PostHogAndroidConfig
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AnalyticsService
    @Inject
    constructor() {
        private var initialized = false
        private var prefs: SharedPreferences? = null
        private var analyticsContextProperties: Map<String, Any> = emptyMap()

        fun initialize(application: Application) {
            if (initialized) return

            prefs = application.getSharedPreferences(PREFS_NAME, Application.MODE_PRIVATE)

            val apiKey = BuildConfig.POSTHOG_API_KEY
            if (apiKey.isBlank()) {
                return
            }

            val isInternalUser = isEmulator() || BuildConfig.DEBUG || isUiTestSession(application)

            val config =
                PostHogAndroidConfig(
                    apiKey = apiKey,
                    host = "https://us.i.posthog.com",
                ).apply {
                    // Emit lifecycle events manually so every event includes our live/dev context tags.
                    captureApplicationLifecycleEvents = false
                    captureDeepLinks = true
                    captureScreenViews = false // We track manually for better control
                    // Session replay: production installs only (enable in PostHog Project Settings → Session replay).
                    // Jetpack Compose requires screenshot mode. No client sampleRate in SDK 3.8.2 — tune in PostHog + debouncerDelayMs.
                    if (!isInternalUser) {
                        sessionReplay = true
                        sessionReplayConfig.maskAllTextInputs = true
                        sessionReplayConfig.maskAllImages = true
                        sessionReplayConfig.captureLogcat = true
                        sessionReplayConfig.screenshot = true
                        sessionReplayConfig.debouncerDelayMs = 1000L
                    }
                }

            PostHogAndroid.setup(application, config)
            analyticsContextProperties =
                mapOf(
                    "platform" to "android",
                    "app_version" to BuildConfig.VERSION_NAME,
                    AnalyticsProperties.ENVIRONMENT to environment(),
                    AnalyticsProperties.BUILD_AUDIENCE to buildAudience(),
                    AnalyticsProperties.BUILD_TYPE to if (BuildConfig.DEBUG) "debug" else "release",
                    AnalyticsProperties.RUNTIME_TARGET to if (isEmulator()) "emulator" else "device",
                    "is_internal" to isInternalUser,
                )
            initialized = true
            identify(
                userId = getOrCreateDistinctId(application),
                properties = analyticsContextProperties,
            )
            trackApplicationLifecycleEvents()

            trackFirstOpenIfNeeded()
        }

        fun track(
            event: String,
            properties: Map<String, Any>? = null,
        ) {
            if (!initialized) return
            PostHog.capture(event, properties = mergeProperties(properties))
        }

        fun screen(
            screenName: String,
            properties: Map<String, Any>? = null,
        ) {
            if (!initialized) return
            PostHog.screen(screenName, mergeProperties(properties))
        }

        fun identify(
            userId: String,
            properties: Map<String, Any>? = null,
        ) {
            if (!initialized) return
            PostHog.identify(userId, mergeProperties(properties))
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

        private fun trackApplicationLifecycleEvents() {
            track(AnalyticsEvents.APPLICATION_OPENED)
            val hasTrackedInstall = prefs?.getBoolean(KEY_HAS_TRACKED_APPLICATION_INSTALLED, false) ?: false
            if (!hasTrackedInstall) {
                track(AnalyticsEvents.APPLICATION_INSTALLED)
                prefs?.edit()?.putBoolean(KEY_HAS_TRACKED_APPLICATION_INSTALLED, true)?.apply()
            }
        }

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

        private fun mergeProperties(properties: Map<String, Any>?): Map<String, Any> =
            if (properties.isNullOrEmpty()) {
                analyticsContextProperties
            } else {
                analyticsContextProperties + properties
            }

        private fun buildAudience(): String {
            if (BuildConfig.DEBUG) return "dev"
            return if (isEmulator()) "dev" else "live"
        }

        private fun environment(): String = if (buildAudience() == "live") "production" else "development"

        private fun isUiTestSession(application: Application): Boolean {
            // Detect Maestro and other UI test frameworks via launch intent extras
            // or system properties set by test runners
            val hasMaestroFlag = System.getProperty("maestro.test") != null
            val hasTestRunner =
                try {
                    Class.forName("androidx.test.espresso.Espresso")
                    true
                } catch (_: ClassNotFoundException) {
                    false
                }
            return hasMaestroFlag || hasTestRunner
        }

        private fun isEmulator(): Boolean {
            val fingerprint = Build.FINGERPRINT.lowercase()
            val model = Build.MODEL.lowercase()
            val manufacturer = Build.MANUFACTURER.lowercase()
            val brand = Build.BRAND.lowercase()
            val device = Build.DEVICE.lowercase()
            val product = Build.PRODUCT.lowercase()
            return (
                fingerprint.startsWith("generic") ||
                    fingerprint.contains("emulator") ||
                    model.contains("sdk_gphone") ||
                    model.contains("emulator") ||
                    model.contains("android sdk built for") ||
                    manufacturer.contains("genymotion") ||
                    (brand.startsWith("generic") && device.startsWith("generic")) ||
                    product.contains("sdk") ||
                    product.contains("emulator")
            )
        }

        companion object {
            private const val PREFS_NAME = "random_timer_analytics"
            private const val KEY_DISTINCT_ID = "posthog_distinct_id"
            private const val KEY_HAS_OPENED = "has_first_opened"
            private const val KEY_HAS_CONFIGURED = "has_first_configured"
            private const val KEY_HAS_COMPLETED = "has_first_completed"
            private const val KEY_HAS_TRACKED_APPLICATION_INSTALLED = "has_tracked_application_installed"
            private val UTM_KEYS =
                listOf(
                    "utm_source",
                    "utm_medium",
                    "utm_campaign",
                    "utm_content",
                    "utm_term",
                )
        }
    }

// Event names for consistency
object AnalyticsEvents {
    const val APPLICATION_INSTALLED = "Application Installed"
    const val APPLICATION_OPENED = "Application Opened"
    const val TIMER_STARTED = "timer_started"
    const val TIMER_COMPLETED = "timer_completed"
    const val TIMER_PAUSED = "timer_paused"
    const val TIMER_RESUMED = "timer_resumed"
    const val TIMER_RESET = "timer_reset"
    const val TIMER_STOPPED = "timer_stopped"
    const val ALARM_TRIGGERED = "alarm_triggered"
    const val ALARM_DISMISSED = "alarm_dismissed"
    const val TIMER_ABANDONED = "timer_abandoned"
    const val TIMER_COUNTDOWN_FINISHED = "timer_countdown_finished"
    const val SETTINGS_CHANGED = "settings_changed"
    const val REVIEW_PROMPT_REQUESTED = "review_prompt_requested"
    const val WRITE_REVIEW_TAPPED = "write_review_tapped"
    const val PAYWALL_VIEWED = "paywall_viewed"
    const val PAYWALL_DISMISSED = "paywall_dismissed"
    const val PAYWALL_PURCHASE_ATTEMPT = "paywall_purchase_attempt"
    const val PAYWALL_PURCHASE_SUCCESS = "paywall_purchase_success"
    const val PAYWALL_PURCHASE_RESULT = "paywall_purchase_result"
    const val PAYWALL_RESTORE_RESULT = "paywall_restore_result"

    // Loop
    const val LOOP_ROUND_COMPLETED = "loop_round_completed"

    // Dwell time
    const val SCREEN_DWELL_TIME = "screen_dwell_time"

    // Purchase failure
    const val PURCHASE_FAILED = "purchase_failed"

    // Feature engagement
    const val VOICE_GENDER_SELECTED = "voice_gender_selected"
    const val FEATURE_GATE_HIT = "feature_gate_hit"

    // Attribution
    const val DEEP_LINK_OPENED = "deep_link_opened"
    const val APPLE_ADS_ATTRIBUTION = "apple_ads_attribution"

    // Onboarding Funnel
    const val FIRST_OPEN = "first_open"
    const val FIRST_TIMER_CONFIGURED = "first_timer_configured"
    const val FIRST_TIMER_COMPLETED = "first_timer_completed"
}

object AnalyticsProperties {
    const val ENTRY_POINT = "entry_point"
    const val RESULT = "result"
    const val SUCCESS = "success"
    const val RESPONSE_CODE = "response_code"
    const val DEBUG_MESSAGE = "debug_message"
    const val SOURCE = "source"
    const val PRODUCT_ID = "product_id"
    const val ENTITLEMENT_LEVEL = "entitlement_level"
    const val ENVIRONMENT = "environment"
    const val BUILD_AUDIENCE = "build_audience"
    const val BUILD_TYPE = "build_type"
    const val RUNTIME_TARGET = "runtime_target"
    const val GENDER = "gender"
    const val FEATURE = "feature"
    const val ALARM_RESPONSE_TIME = "alarm_response_time"
    const val ABANDON_REASON = "abandon_reason"
    const val SCREEN = "screen"
    const val REASON = "reason"
}

object AnalyticsScreens {
    const val TIMER_SETUP = "Timer Setup"
    const val ACTIVE_TIMER = "Active Timer"
}
