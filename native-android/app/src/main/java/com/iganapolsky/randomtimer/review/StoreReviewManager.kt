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

internal fun reviewPromptMilestoneForCompletionCount(count: Int): Int? =
    when {
        count < 3 -> null
        count < 10 -> 3
        count < 25 -> 10
        else -> 25 + ((count - 25) / 25) * 25
    }

internal fun isEligibleForReviewPrompt(
    completionCount: Int,
    lastPromptMilestone: Int,
    lastReviewTimestampMillis: Long,
    nowMillis: Long,
    minDaysBetweenRequests: Long,
): Boolean {
    val milestone = reviewPromptMilestoneForCompletionCount(completionCount) ?: return false
    if (milestone <= lastPromptMilestone) return false
    if (lastReviewTimestampMillis == 0L) return true
    val daysSinceLast = (nowMillis - lastReviewTimestampMillis) / (1000 * 60 * 60 * 24)
    return daysSinceLast >= minDaysBetweenRequests
}

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
            private const val KEY_LAST_PROMPT_MILESTONE = "last_prompt_milestone"

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
                        .putInt(
                            KEY_LAST_PROMPT_MILESTONE,
                            reviewPromptMilestoneForCompletionCount(
                                prefs.getInt(KEY_COMPLETION_COUNT, 0),
                            ) ?: 0,
                        ).apply()
                }
            }
        }

        private fun isEligibleForReview(): Boolean =
            isEligibleForReviewPrompt(
                completionCount = prefs.getInt(KEY_COMPLETION_COUNT, 0),
                lastPromptMilestone = prefs.getInt(KEY_LAST_PROMPT_MILESTONE, 0),
                lastReviewTimestampMillis = prefs.getLong(KEY_LAST_REVIEW_TIMESTAMP, 0L),
                nowMillis = System.currentTimeMillis(),
                minDaysBetweenRequests = MIN_DAYS_BETWEEN_REQUESTS,
            )

        private fun getAppVersion(): String =
            try {
                context.packageManager.getPackageInfo(context.packageName, 0).versionName ?: "unknown"
            } catch (_: Exception) {
                "unknown"
            }
    }
