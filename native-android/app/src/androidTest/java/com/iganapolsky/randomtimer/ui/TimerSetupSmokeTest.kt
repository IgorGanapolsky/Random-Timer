package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithContentDescription
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.iganapolsky.randomtimer.MainActivity
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class TimerSetupSmokeTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Before
    fun setup() {
        DeviceTestSupport.clearAppData()
    }

    @Test
    fun setupScreenRendersCoreControls() {
        DeviceTestSupport.waitForSetupScreen(composeRule)

        composeRule.onNodeWithTag("start_timer", useUnmergedTree = true).assertExists()
        composeRule.onNodeWithContentDescription("Minimum time slider").assertExists()
        composeRule.onNodeWithContentDescription("Maximum time slider").assertExists()
    }

    @Test
    fun soundArsenalLockOpensPaywallForUpgrade() {
        DeviceTestSupport.waitForSetupScreen(composeRule)

        composeRule.waitUntil(timeoutMillis = DeviceTestSupport.SETUP_READY_TIMEOUT_MS) {
            composeRule
                .onAllNodesWithContentDescription("Unlock Sound Arsenal", useUnmergedTree = true)
                .fetchSemanticsNodes()
                .isNotEmpty()
        }

        composeRule
            .onNodeWithContentDescription("Unlock Sound Arsenal", useUnmergedTree = true)
            .performScrollTo()
            .performClick()

        composeRule.waitForIdle()
        composeRule.waitUntil(timeoutMillis = DeviceTestSupport.SETUP_READY_TIMEOUT_MS) {
            composeRule
                .onAllNodesWithText("Unlock Full Fight-Ready Training")
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
    }
}
