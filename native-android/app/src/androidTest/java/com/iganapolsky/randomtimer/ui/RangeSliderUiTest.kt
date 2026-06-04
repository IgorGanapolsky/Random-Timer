package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performSemanticsAction
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.iganapolsky.randomtimer.MainActivity
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class RangeSliderUiTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    private var firstTest = true

    @Before
    fun prepareTest() {
        if (firstTest) {
            firstTest = false
        } else {
            DeviceTestSupport.prepareNextTest(composeRule)
        }
    }

    @After
    fun tearDown() {
        DeviceTestSupport.stopTimerService()
    }

    @Test
    fun draggingMinBeyondGapPushesMaxForward() {
        DeviceTestSupport.waitForSetupScreen(composeRule)

        composeRule
            .onNodeWithContentDescription("Maximum time slider", useUnmergedTree = true)
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(60f)
            }
        composeRule.waitForIdle()
        composeRule.onNodeWithText("Maximum: 1m", useUnmergedTree = true).assertExists()

        composeRule
            .onNodeWithContentDescription("Minimum time slider", useUnmergedTree = true)
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(50f)
            }
        composeRule.waitForIdle()
        composeRule.onNodeWithText("Minimum: 50s", useUnmergedTree = true).assertExists()
        composeRule.onNodeWithText("Maximum: 55s", useUnmergedTree = true).assertExists()
    }

    @Test
    fun draggingMaxBelowGapPullsMinBack() {
        DeviceTestSupport.waitForSetupScreen(composeRule)

        composeRule
            .onNodeWithContentDescription("Minimum time slider", useUnmergedTree = true)
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(150f)
            }
        composeRule.waitForIdle()
        composeRule.onNodeWithText("Minimum: 2m 30s", useUnmergedTree = true).assertExists()

        composeRule
            .onNodeWithContentDescription("Maximum time slider", useUnmergedTree = true)
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(160f)
            }
        composeRule.waitForIdle()
        composeRule.onNodeWithText("Maximum: 2m 40s", useUnmergedTree = true).assertExists()
        composeRule.onNodeWithText("Minimum: 2m 35s", useUnmergedTree = true).assertExists()
    }
}
