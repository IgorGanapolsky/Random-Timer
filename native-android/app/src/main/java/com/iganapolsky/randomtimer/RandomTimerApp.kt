package com.iganapolsky.randomtimer

import android.app.Application
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class RandomTimerApp : Application() {

    @Inject lateinit var analyticsService: AnalyticsService

    override fun onCreate() {
        super.onCreate()
        analyticsService.initialize(this)
    }
}
