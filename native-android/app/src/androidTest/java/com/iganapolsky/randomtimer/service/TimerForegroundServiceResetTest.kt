package com.iganapolsky.randomtimer.service

import android.content.Intent
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.rule.ServiceTestRule
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.time.Duration
import org.junit.Assert.assertEquals

@RunWith(AndroidJUnit4::class)
class TimerForegroundServiceResetTest {

    @get:Rule
    val serviceRule = ServiceTestRule()

    @Test
    fun resetWhileAlarmStopsAlarmAndRestartsTimer() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext

        val startIntent = Intent(context, TimerForegroundService::class.java).apply {
            action = TimerForegroundService.ACTION_START
            putExtra(TimerForegroundService.EXTRA_TARGET_DURATION_MS, 1000L)
            putExtra(TimerForegroundService.EXTRA_REMAINING_DURATION_MS, 1000L)
            putExtra(TimerForegroundService.EXTRA_MIN_SECONDS, 1)
            putExtra(TimerForegroundService.EXTRA_MAX_SECONDS, 1)
            putExtra(TimerForegroundService.EXTRA_ALARM_DURATION, 5)
            putExtra(TimerForegroundService.EXTRA_HIDDEN_MODE, false)
            putExtra(TimerForegroundService.EXTRA_REPEAT_ENABLED, false)
            putExtra(TimerForegroundService.EXTRA_SOUND_TYPE, "INTENSE")
            putExtra(TimerForegroundService.EXTRA_VOLUME, 0f)
            putExtra(TimerForegroundService.EXTRA_VIBRATION_ENABLED, false)
        }

        serviceRule.startService(startIntent)

        val binder = serviceRule.bindService(
            Intent(context, TimerForegroundService::class.java)
        ) as TimerForegroundService.LocalBinder
        val service = binder.getService()

        // Wait for the timer to expire and alarm state to start.
        Thread.sleep(1200)

        val state = service.timerState.value
        assertEquals(TimerStatus.ALARM, state?.status)

        val resetIntent = Intent(service, TimerForegroundService::class.java).apply {
            action = TimerForegroundService.ACTION_RESET
        }
        service.onStartCommand(resetIntent, 0, 0)

        Thread.sleep(200)

        val updatedState = service.timerState.value
        assertEquals(TimerStatus.RUNNING, updatedState?.status)
        assertEquals(Duration.ZERO, updatedState?.alarmTimeRemaining ?: Duration.ZERO)
        assertEquals(updatedState?.targetDuration, updatedState?.remainingDuration)
    }
}
