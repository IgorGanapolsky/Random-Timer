package com.iganapolsky.randomtimer

import android.app.Application
import com.google.firebase.analytics.FirebaseAnalytics
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.runtime.RuntimeConfigurationService
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltAndroidApp
class RandomTimerApp : Application() {
    @Inject lateinit var analyticsService: AnalyticsService

    @Inject lateinit var runtimeConfigurationService: RuntimeConfigurationService

    @Inject lateinit var appScope: CoroutineScope

    override fun onCreate() {
        super.onCreate()

        // PostHog is our source of truth for product analytics.
        // Disable Firebase Analytics event collection to avoid duplicate telemetry streams.
        runCatching {
            FirebaseAnalytics.getInstance(this).setAnalyticsCollectionEnabled(false)
        }

        analyticsService.initialize(this)

        appScope.launch {
            runtimeConfigurationService.snapshot.collect { snapshot ->
                analyticsService.updateRuntimeContext(snapshot.analyticsProperties())
            }
        }
        appScope.launch {
            runtimeConfigurationService.refresh(analyticsService.currentDistinctId())
        }
    }
}
