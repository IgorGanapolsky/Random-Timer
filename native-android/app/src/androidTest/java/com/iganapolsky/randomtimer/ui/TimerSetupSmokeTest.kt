package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.hasScrollAction
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollToNode
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.iganapolsky.randomtimer.MainActivity
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class TimerSetupSmokeTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun setupScreenRendersCoreControls() {
        composeRule.waitUntil(timeoutMillis = 5_000) {
            composeRule
                .onAllNodesWithText("Start First Drill")
                .fetchSemanticsNodes()
                .isNotEmpty()
        }

        composeRule
            .onNodeWithText("Start First Drill")
            .assertExists()

        composeRule
            .onNodeWithContentDescription("Minimum time slider")
            .assertExists()

        composeRule
            .onNodeWithContentDescription("Maximum time slider")
            .assertExists()
    }

    @Test
    fun soundArsenalLockOpensPaywallForUpgrade() {
        composeRule
            .onNode(hasScrollAction())
            .performScrollToNode(hasContentDescription("Unlock Sound Arsenal"))

        composeRule
            .onNodeWithContentDescription("Unlock Sound Arsenal", useUnmergedTree = true)
            .assertExists()
            .performClick()

        composeRule.waitUntil(timeoutMillis = 5_000) {
            composeRule
                .onAllNodesWithText("Unlock Full Fight-Ready Training")
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
    }
}
