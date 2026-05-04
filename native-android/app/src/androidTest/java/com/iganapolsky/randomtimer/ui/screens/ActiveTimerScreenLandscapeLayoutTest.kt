package com.iganapolsky.randomtimer.ui.screens

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.size
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.unit.dp
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
class ActiveTimerScreenLandscapeLayoutTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun stopButtonIsVisibleAndTappableInLandscapeConstraints() {
        val state =
            TimerState(
                config = TimerConfig.DEFAULT,
                targetDuration = 30.seconds,
                remainingDuration = 30.seconds,
                status = TimerStatus.RUNNING,
            )

        var stopped = false

        composeRule.setContent {
            RandomTimerTheme {
                ActiveTimerScreen(
                    state = state,
                    isPro = false,
                    onStop = { stopped = true },
                    onDismissAlarm = {},
                    onSilence = {},
                    onPause = {},
                    onResume = {},
                    onReset = {},
                    onLoopToggle = {},
                    onVoiceToggle = {},
                    // Force "landscape" branch by giving a wide constraint box.
                    modifier = Modifier.size(width = 800.dp, height = 400.dp),
                )
            }
        }

        composeRule.onNodeWithText("Stop").assertIsDisplayed()
        composeRule.onNodeWithText("Stop").performClick()

        composeRule.runOnIdle {
            assertTrue(stopped)
        }
    }
}
