package com.iganapolsky.randomtimer.review

import android.app.Activity
import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.google.android.play.core.review.ReviewManagerFactory
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.reviewDataStore by preferencesDataStore(name = "review_prefs")

@Singleton
class StoreReviewManager @Inject constructor(
    private val context: Context
) {
    companion object {
        private val COMPLETION_COUNT = intPreferencesKey("timer_completion_count")
        private val LAST_REVIEW_REQUEST = longPreferencesKey("last_review_request")
        private const val COMPLETIONS_BEFORE_REVIEW = 3
        private const val MIN_DAYS_BETWEEN_REQUESTS = 30L
    }

    suspend fun onTimerCompleted() {
        context.reviewDataStore.edit { prefs ->
            val currentCount = prefs[COMPLETION_COUNT] ?: 0
            prefs[COMPLETION_COUNT] = currentCount + 1
        }
    }

    suspend fun shouldRequestReview(): Boolean {
        val prefs = context.reviewDataStore.data.first()
        val completionCount = prefs[COMPLETION_COUNT] ?: 0
        val lastRequest = prefs[LAST_REVIEW_REQUEST] ?: 0L

        val daysSinceLastRequest = (System.currentTimeMillis() - lastRequest) / (1000 * 60 * 60 * 24)

        return completionCount >= COMPLETIONS_BEFORE_REVIEW &&
               (lastRequest == 0L || daysSinceLastRequest >= MIN_DAYS_BETWEEN_REQUESTS)
    }

    suspend fun requestReview(activity: Activity) {
        if (!shouldRequestReview()) return

        val reviewManager = ReviewManagerFactory.create(context)
        val requestFlow = reviewManager.requestReviewFlow()

        requestFlow.addOnCompleteListener { task ->
            if (task.isSuccessful) {
                val reviewInfo = task.result
                reviewManager.launchReviewFlow(activity, reviewInfo)
            }
        }

        // Mark that we requested a review
        context.reviewDataStore.edit { prefs ->
            prefs[LAST_REVIEW_REQUEST] = System.currentTimeMillis()
        }
    }

    fun getCompletionCount() = context.reviewDataStore.data.map { prefs ->
        prefs[COMPLETION_COUNT] ?: 0
    }
}
