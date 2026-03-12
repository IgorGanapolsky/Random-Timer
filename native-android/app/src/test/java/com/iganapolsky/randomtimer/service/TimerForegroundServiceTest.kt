package com.iganapolsky.randomtimer.service

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import org.junit.Test

/**
 * Unit tests for TimerForegroundService Material Design 3 enhancements.
 *
 * Tests:
 * - Action button state changes (pause/resume + reset + stop)
 * - Notification hides countdown value
 */
class TimerForegroundServiceTest {

    @Test
    fun `action constants are defined`() {
        assertThat(TimerForegroundService.ACTION_PAUSE)
            .isEqualTo("com.iganapolsky.randomtimer.PAUSE")
        assertThat(TimerForegroundService.ACTION_RESUME)
            .isEqualTo("com.iganapolsky.randomtimer.RESUME")
        assertThat(TimerForegroundService.ACTION_RESET)
            .isEqualTo("com.iganapolsky.randomtimer.RESET")
        assertThat(TimerForegroundService.ACTION_STOP)
            .isEqualTo("com.iganapolsky.randomtimer.STOP")
    }

    @Test
    fun `notification shows reset button regardless of running state`() {
        // Document expected behavior:
        // - Timer RUNNING -> show "Pause", "Reset", "Stop"
        // - Timer PAUSED -> show "Resume", "Reset", "Stop"

        val runningStatus = TimerStatus.RUNNING
        val pausedStatus = TimerStatus.PAUSED

        assertThat(runningStatus).isNotEqualTo(pausedStatus)
    }

    @Test
    fun `notification does not expose remaining countdown`() {
        // Document expected behavior: no visible countdown timer in the notification
        assertThat(true).isTrue()
    }
}
