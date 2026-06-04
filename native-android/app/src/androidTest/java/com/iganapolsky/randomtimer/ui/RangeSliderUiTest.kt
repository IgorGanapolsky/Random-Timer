package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.junit4.AndroidComposeTestRule
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performSemanticsAction
import androidx.test.ext.junit.rules.ActivityScenarioRule
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

        setSliderProgress("Maximum time slider", 60f)
        waitForLabel(composeRule, "Maximum: 1m")

        setSliderProgress("Minimum time slider", 50f)
        waitForLabel(composeRule, "Minimum: 50s")
        waitForLabel(composeRule, "Maximum: 55s")
    }

    @Test
    fun draggingMaxBelowGapPullsMinBack() {
        DeviceTestSupport.waitForSetupScreen(composeRule)

        setSliderProgress("Minimum time slider", 100f)
        waitForLabel(composeRule, "Minimum: 1m 40s")

        setSliderProgress("Maximum time slider", 200f)
        waitForLabel(composeRule, "Maximum: 3m 20s")

        setSliderProgress("Maximum time slider", 50f)
        waitForLabel(composeRule, "Maximum: 50s")
        waitForLabel(composeRule, "Minimum: 45s")
    }

    private fun setSliderProgress(
        contentDescription: String,
        progress: Float,
    ) {
        composeRule
            .onNodeWithContentDescription(contentDescription, useUnmergedTree = true)
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(progress)
            }
        composeRule.waitForIdle()
    }

    private fun waitForLabel(
        rule: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>,
        text: String,
    ) {
        rule.waitUntil(timeoutMillis = DeviceTestSupport.SETUP_READY_TIMEOUT_MS) {
            rule.onAllNodesWithText(text, useUnmergedTree = true)
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
        rule.onNodeWithText(text, useUnmergedTree = true).assertExists()
    }
}
