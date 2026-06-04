package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.test.click
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.percentOffset
import androidx.compose.ui.test.performTouchInput
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

        tapSliderToSeconds("Maximum time slider", 60, rangeEnd = TimerConfig.MAX_SECONDS_FREE.toFloat())
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 1m")

        tapSliderToSeconds(
            "Minimum time slider",
            56,
            rangeEnd = (TimerConfig.MAX_SECONDS_FREE - 5).toFloat(),
        )
        DeviceTestSupport.waitForLabel(composeRule, "Minimum: 56s")
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 1m 1s")
    }

    @Test
    fun draggingMaxBelowGapPullsMinBack() {
        DeviceTestSupport.waitForSetupScreen(composeRule)

        tapSliderToSeconds(
            "Minimum time slider",
            100,
            rangeEnd = (TimerConfig.MAX_SECONDS_FREE - 5).toFloat(),
        )
        DeviceTestSupport.waitForLabel(composeRule, "Minimum: 1m 40s")

        tapSliderToSeconds("Maximum time slider", 200, rangeEnd = TimerConfig.MAX_SECONDS_FREE.toFloat())
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 3m 20s")

        tapSliderToSeconds("Maximum time slider", 50, rangeEnd = TimerConfig.MAX_SECONDS_FREE.toFloat())
        DeviceTestSupport.waitForLabel(composeRule, "Maximum: 50s")
        DeviceTestSupport.waitForLabel(composeRule, "Minimum: 45s")
    }

    private fun tapSliderToSeconds(
        contentDescription: String,
        targetSeconds: Int,
        rangeStart: Float = 5f,
        rangeEnd: Float,
    ) {
        val fraction =
            ((targetSeconds - rangeStart) / (rangeEnd - rangeStart))
                .coerceIn(0f, 1f)
        DeviceTestSupport.scrollToTimeRangeSliders(composeRule)
        composeRule
            .onNodeWithContentDescription(contentDescription, useUnmergedTree = true)
            .performTouchInput {
                click(percentOffset(fraction, 0.5f))
            }
        composeRule.waitForIdle()
    }
}
