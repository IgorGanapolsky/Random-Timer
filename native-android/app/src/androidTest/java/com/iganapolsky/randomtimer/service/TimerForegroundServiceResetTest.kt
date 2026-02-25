package com.iganapolsky.randomtimer.service

import android.content.Intent
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.rule.ServiceTestRule
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds

@RunWith(AndroidJUnit4::class)
class TimerForegroundServiceResetTest {
    @get:Rule
    val serviceRule = ServiceTestRule()

    private fun waitForCondition(
        timeoutMs: Long = 3_000,
        pollMs: Long = 50,
        condition: () -> Boolean,
    ) {
        runBlocking {
            withTimeout(timeoutMs) {
                while (!condition()) {
                    delay(pollMs)
                }
            }
        }
    }

    @Test
    fun resetWhileAlarmStopsAlarmAndRestartsTimer() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext

        val startIntent =
            Intent(context, TimerForegroundService::class.java).apply {
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

        val binder =
            serviceRule.bindService(
                Intent(context, TimerForegroundService::class.java),
            ) as TimerForegroundService.LocalBinder
        val service = binder.getService()

        // Wait for timer state to transition into alarm.
        waitForCondition(timeoutMs = 4_000) {
            service.timerState.value?.status == TimerStatus.ALARM
        }

        val state = service.timerState.value
        assertEquals(TimerStatus.ALARM, state?.status)

        val resetIntent =
            Intent(service, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_RESET
            }
        service.onStartCommand(resetIntent, 0, 0)

        waitForCondition {
            val state = service.timerState.value
            state?.status == TimerStatus.RUNNING &&
                (state.alarmTimeRemaining ?: Duration.ZERO) == Duration.ZERO &&
                state.targetDuration == state.remainingDuration
        }

        val updatedState = service.timerState.value
        assertEquals(TimerStatus.RUNNING, updatedState?.status)
        assertEquals(Duration.ZERO, updatedState?.alarmTimeRemaining ?: Duration.ZERO)
        assertEquals(updatedState?.targetDuration, updatedState?.remainingDuration)
    }

    @Test
    fun resetWhileRunningRestartsFromFullDuration() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext

        val startIntent =
            Intent(context, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_START
                putExtra(TimerForegroundService.EXTRA_TARGET_DURATION_MS, 5000L)
                putExtra(TimerForegroundService.EXTRA_REMAINING_DURATION_MS, 3000L)
                putExtra(TimerForegroundService.EXTRA_MIN_SECONDS, 5)
                putExtra(TimerForegroundService.EXTRA_MAX_SECONDS, 5)
                putExtra(TimerForegroundService.EXTRA_ALARM_DURATION, 5)
                putExtra(TimerForegroundService.EXTRA_HIDDEN_MODE, false)
                putExtra(TimerForegroundService.EXTRA_REPEAT_ENABLED, false)
                putExtra(TimerForegroundService.EXTRA_SOUND_TYPE, "INTENSE")
                putExtra(TimerForegroundService.EXTRA_VOLUME, 0f)
                putExtra(TimerForegroundService.EXTRA_VIBRATION_ENABLED, false)
            }

        serviceRule.startService(startIntent)

        val binder =
            serviceRule.bindService(
                Intent(context, TimerForegroundService::class.java),
            ) as TimerForegroundService.LocalBinder
        val service = binder.getService()

        waitForCondition {
            service.timerState.value?.status == TimerStatus.RUNNING
        }

        val initialState = service.timerState.value
        assertEquals(TimerStatus.RUNNING, initialState?.status)

        val resetIntent =
            Intent(service, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_RESET
            }
        service.onStartCommand(resetIntent, 0, 0)

        waitForCondition {
            val state = service.timerState.value
            state?.status == TimerStatus.RUNNING &&
                state.remainingDuration == 5000.milliseconds &&
                state.targetDuration == state.remainingDuration &&
                (state.alarmTimeRemaining ?: Duration.ZERO) == Duration.ZERO
        }

        val updatedState = service.timerState.value
        assertEquals(TimerStatus.RUNNING, updatedState?.status)
        assertEquals(5000.milliseconds, updatedState?.remainingDuration)
        assertEquals(updatedState?.targetDuration, updatedState?.remainingDuration)
        assertEquals(Duration.ZERO, updatedState?.alarmTimeRemaining ?: Duration.ZERO)
    }
}
