package com.iganapolsky.randomtimer

import android.app.Application
import androidx.appfunctions.service.AppFunctionConfiguration
import com.google.firebase.analytics.FirebaseAnalytics
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.appfunctions.RandomTimerAppFunctionEntryPoint
import com.iganapolsky.randomtimer.appfunctions.RandomTimerAppFunctions
import dagger.hilt.android.EntryPointAccessors
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class RandomTimerApp :
    Application(),
    AppFunctionConfiguration.Provider {
    @Inject lateinit var analyticsService: AnalyticsService

    override val appFunctionConfiguration: AppFunctionConfiguration by lazy {
        AppFunctionConfiguration
            .Builder()
            .addEnclosingClassFactory(RandomTimerAppFunctions::class.java) {
                val entryPoint =
                    EntryPointAccessors.fromApplication(
                        this,
                        RandomTimerAppFunctionEntryPoint::class.java,
                    )
                RandomTimerAppFunctions(entryPoint.randomTimerAppFunctionHandler())
            }.build()
    }

    override fun onCreate() {
        super.onCreate()

        // PostHog is our source of truth for product analytics.
        // Disable Firebase Analytics event collection to avoid duplicate telemetry streams.
        runCatching {
            FirebaseAnalytics.getInstance(this).setAnalyticsCollectionEnabled(false)
        }

        analyticsService.initialize(this)
    }
}
