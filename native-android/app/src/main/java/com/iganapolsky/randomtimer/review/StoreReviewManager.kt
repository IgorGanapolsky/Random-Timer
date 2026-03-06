package com.iganapolsky.randomtimer.review

import android.app.Activity
import android.content.Context
import android.content.SharedPreferences
import com.google.android.play.core.review.ReviewManagerFactory
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class StoreReviewManager
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
        private val analyticsService: AnalyticsService,
    ) {
        private val prefs: SharedPreferences =
            context.getSharedPreferences("review_prefs", Context.MODE_PRIVATE)

        companion object {
            private const val KEY_COMPLETION_COUNT = "completion_count"
            private const val KEY_LAST_REVIEW_TIMESTAMP = "last_review_timestamp"
            private const val KEY_LAST_REVIEW_VERSION = "last_review_version"
            private const val KEY_PENDING_REVIEW = "pending_review"

            private const val COMPLETIONS_BEFORE_REVIEW = 1
            private const val MIN_DAYS_BETWEEN_REQUESTS = 30L
        }

        fun recordCompletion() {
            val count = prefs.getInt(KEY_COMPLETION_COUNT, 0) + 1
            prefs.edit().putInt(KEY_COMPLETION_COUNT, count).apply()

            if (isEligibleForReview()) {
                prefs.edit().putBoolean(KEY_PENDING_REVIEW, true).apply()
            }
        }

        fun hasPendingReview(): Boolean = prefs.getBoolean(KEY_PENDING_REVIEW, false)

        fun requestReview(activity: Activity) {
            if (!hasPendingReview()) return

            prefs.edit().putBoolean(KEY_PENDING_REVIEW, false).apply()
            analyticsService.track(AnalyticsEvents.REVIEW_PROMPT_REQUESTED)

            val reviewManager = ReviewManagerFactory.create(context)
            val request = reviewManager.requestReviewFlow()
            request.addOnCompleteListener { task ->
                if (task.isSuccessful) {
                    analyticsService.track(AnalyticsEvents.WRITE_REVIEW_TAPPED)
                    reviewManager.launchReviewFlow(activity, task.result)
                    prefs
                        .edit()
                        .putLong(KEY_LAST_REVIEW_TIMESTAMP, System.currentTimeMillis())
                        .putString(KEY_LAST_REVIEW_VERSION, getAppVersion())
                        .apply()
                }
            }
        }

        private fun isEligibleForReview(): Boolean {
            val count = prefs.getInt(KEY_COMPLETION_COUNT, 0)
            val lastTimestamp = prefs.getLong(KEY_LAST_REVIEW_TIMESTAMP, 0L)
            val lastVersion = prefs.getString(KEY_LAST_REVIEW_VERSION, null)
            val currentVersion = getAppVersion()

            if (count < COMPLETIONS_BEFORE_REVIEW) return false
            if (lastTimestamp == 0L) return true
            if (lastVersion != currentVersion) return true

            val daysSinceLast = (System.currentTimeMillis() - lastTimestamp) / (1000 * 60 * 60 * 24)
            return daysSinceLast >= MIN_DAYS_BETWEEN_REQUESTS
        }

        private fun getAppVersion(): String =
            try {
                context.packageManager.getPackageInfo(context.packageName, 0).versionName ?: "unknown"
            } catch (_: Exception) {
                "unknown"
            }
    }
