package com.iganapolsky.randomtimer.ui.screens

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.click
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.performTouchInput
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import org.junit.Assert.assertTrue
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
        // Per docs/TASKS.md: "When status is ALARM or COMPLETE, tapping the
        // timer circle has the same effect as the Stop button." The screen
        // wires the tap to onDismissAlarm under `isComplete` (which covers
        // both COMPLETE and ALARM, see ActiveTimerScreen.kt:78). Previously
        // wired to onSilence; that param was removed in the bluetooth-headset
        // + tap-to-dismiss commit (284291be).
        val state =
            TimerState(
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
                    isPro = false,
                    onStop = {},
                    onDismissAlarm = { dismissed = true },
                    onPause = {},
                    onResume = {},
                    onReset = {},
                    onLoopToggle = {},
                    onVoiceToggle = {},
                )
            }
        }

        // CircularTimer exposes "Timer complete" accessibility label for ALARM/COMPLETE.
        composeRule
            .onNodeWithContentDescription("Timer complete")
            .performTouchInput { click() }

        composeRule.runOnIdle {
            assertTrue(dismissed)
        }
    }

    @Test
    fun tappingCircleWhenRunningDoesNothing() {
        val state =
            TimerState(
                config = TimerConfig.DEFAULT,
                targetDuration = 60.seconds,
                remainingDuration = 30.seconds,
                status = TimerStatus.RUNNING,
            )

        var dismissed = false

        composeRule.setContent {
            RandomTimerTheme {
                ActiveTimerScreen(
                    state = state,
                    isPro = false,
                    onStop = {},
                    onDismissAlarm = { dismissed = true },
                    onPause = {},
                    onResume = {},
                    onReset = {},
                    onLoopToggle = {},
                    onVoiceToggle = {},
                )
            }
        }

        // RUNNING state shows "Timer running" accessibility label, not "Timer complete"
        // The circle should NOT be clickable during RUNNING state
        composeRule
            .onNodeWithContentDescription("Timer running")
            .performTouchInput { click() }

        composeRule.runOnIdle {
            assertTrue(!dismissed)
        }
    }

    @Test
    fun freeRunningTimerDoesNotRenderVoiceCalloutBadge() {
        val state =
            TimerState(
                config = TimerConfig.DEFAULT.copy(voiceEnabled = true),
                targetDuration = 60.seconds,
                remainingDuration = 30.seconds,
                status = TimerStatus.RUNNING,
            )

        composeRule.setContent {
            RandomTimerTheme {
                ActiveTimerScreen(
                    state = state,
                    isPro = false,
                    onStop = {},
                    onDismissAlarm = {},
                    onPause = {},
                    onResume = {},
                    onReset = {},
                    onLoopToggle = {},
                    onVoiceToggle = {},
                )
            }
        }

        assertTrue(composeRule.onAllNodesWithText("Voice Callouts On").fetchSemanticsNodes().isEmpty())
        assertTrue(composeRule.onAllNodesWithText("Voice Callouts Locked").fetchSemanticsNodes().isEmpty())
    }

    @Test
    fun tappingCircleWhenCompleteCallsOnDismissAlarm() {
        // Per docs/TASKS.md: tap during ALARM or COMPLETE is equivalent to Stop.
        // Updated 2026-05-18 — the prior expectation that COMPLETE tap was a no-op
        // contradicted the spec; commit 284291be aligned the implementation to
        // the spec via the `isComplete` predicate (ActiveTimerScreen.kt:78).
        val state =
            TimerState(
                config = TimerConfig.DEFAULT,
                targetDuration = 5.seconds,
                remainingDuration = 0.seconds,
                status = TimerStatus.COMPLETE,
            )

        var dismissed = false

        composeRule.setContent {
            RandomTimerTheme {
                ActiveTimerScreen(
                    state = state,
                    isPro = false,
                    onStop = {},
                    onDismissAlarm = { dismissed = true },
                    onPause = {},
                    onResume = {},
                    onReset = {},
                    onLoopToggle = {},
                    onVoiceToggle = {},
                )
            }
        }

        composeRule
            .onNodeWithContentDescription("Timer complete")
            .performTouchInput { click() }

        composeRule.runOnIdle {
            assertTrue(dismissed)
        }
    }
}
