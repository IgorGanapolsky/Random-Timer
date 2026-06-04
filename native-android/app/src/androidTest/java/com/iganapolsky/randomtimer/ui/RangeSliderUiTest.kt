package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.performSemanticsAction
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.iganapolsky.randomtimer.MainActivity
import com.iganapolsky.randomtimer.domain.model.TimerConfig
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

        setSliderSeconds("Maximum time slider", 60f)
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 1m")

        setSliderSeconds(
            "Minimum time slider",
            56f,
            rangeEnd = (TimerConfig.MAX_SECONDS_FREE - 5).toFloat(),
        )
        DeviceTestSupport.waitForLabel(composeRule, "Minimum: 56s")
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 1m 1s")
    }

    @Test
    fun draggingMaxBelowGapPullsMinBack() {
        DeviceTestSupport.waitForSetupScreen(composeRule)

        setSliderSeconds(
            "Minimum time slider",
            100f,
            rangeEnd = (TimerConfig.MAX_SECONDS_FREE - 5).toFloat(),
        )
        DeviceTestSupport.waitForLabel(composeRule, "Minimum: 1m 40s")

        setSliderSeconds("Maximum time slider", 200f)
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 3m 20s")

        setSliderSeconds("Maximum time slider", 50f)
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 50s")
        DeviceTestSupport.waitForLabel(composeRule, "Minimum: 45s")
    }

    private fun setSliderSeconds(
        contentDescription: String,
        seconds: Float,
        rangeEnd: Float = TimerConfig.MAX_SECONDS_FREE.toFloat(),
    ) {
        require(seconds in 5f..rangeEnd) { "seconds=$seconds out of slider range end=$rangeEnd" }
        DeviceTestSupport.scrollToTimeRangeSliders(composeRule)
        composeRule
            .onNodeWithContentDescription(contentDescription, useUnmergedTree = true)
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(seconds)
            }
        composeRule.waitForIdle()
    }
}
