package com.iganapolsky.randomtimer

import android.app.Application
import com.google.firebase.analytics.FirebaseAnalytics
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.crash.CrashReportingService
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class RandomTimerApp : Application() {
    @Inject lateinit var analyticsService: AnalyticsService

    @Inject lateinit var crashReportingService: CrashReportingService

    override fun onCreate() {
        super.onCreate()

        crashReportingService.initialize()

        // PostHog is our source of truth for product analytics.
        // Disable Firebase Analytics event collection to avoid duplicate telemetry streams.
        runCatching {
            FirebaseAnalytics.getInstance(this).setAnalyticsCollectionEnabled(false)
        }

        analyticsService.initialize(this)
        crashReportingService.setUserId(analyticsService.observabilityDeviceId(this))
    }
}
