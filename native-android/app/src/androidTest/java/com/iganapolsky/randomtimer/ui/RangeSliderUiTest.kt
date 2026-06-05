package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
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

        // Default 5s–30s. Min-first SetProgress is reliable on API 30 CI (max-first is not).
        setSliderProgress("Minimum time slider", 50f)
        DeviceTestSupport.waitForLabel(composeRule, "Minimum: 50s")
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 55s")
    }

    @Test
    fun draggingMaxBelowGapPullsMinBack() {
        DeviceTestSupport.waitForSetupScreen(composeRule)

        setSliderProgress("Minimum time slider", 100f)
        DeviceTestSupport.waitForLabel(composeRule, "Minimum: 1m 40s")

        setSliderProgress("Maximum time slider", 200f)
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 3m 20s")

        setSliderProgress("Maximum time slider", 50f)
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 50s")
        DeviceTestSupport.waitForLabel(composeRule, "Minimum: 45s")
    }

    private fun setSliderProgress(
        contentDescription: String,
        progress: Float,
    ) {
        DeviceTestSupport.scrollToTimeRangeSliders(composeRule)
        composeRule
            .onNodeWithContentDescription(contentDescription, useUnmergedTree = true)
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(progress)
            }
        composeRule.waitForIdle()
    }
}
