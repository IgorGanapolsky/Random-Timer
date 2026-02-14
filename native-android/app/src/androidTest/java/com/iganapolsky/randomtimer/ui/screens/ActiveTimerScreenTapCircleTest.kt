package com.iganapolsky.randomtimer.ui.screens

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.click
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.time.Duration.Companion.seconds

@RunWith(AndroidJUnit4::class)
class ActiveTimerScreenTapCircleTest {

    @get:Rule
    val composeRule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun tappingCircleWhenAlarmCallsOnDismissAlarm() {
        val state = TimerState(
            config = TimerConfig.DEFAULT,
            targetDuration = 5.seconds,
            remainingDuration = 0.seconds,
            status = TimerStatus.ALARM,
            alarmTimeRemaining = 10.seconds,
        )

        var dismissed = false

        composeRule.setContent {
            RandomTimerTheme {
                ActiveTimerScreen(
                    state = state,
                    onStop = {},
                    onDismissAlarm = { dismissed = true },
                    onSilence = {},
                    onPause = {},
                    onResume = {},
                    onReset = {},
                    onLoopToggle = {},
                )
            }
        }

        // CircularTimer exposes "Timer complete" accessibility label for ALARM/COMPLETE.
        composeRule
            .onNodeWithContentDescription("Timer complete")
            .performTouchInput { click() }

        composeRule.runOnIdle {
            assertThat(dismissed).isTrue()
        }
    }
}

