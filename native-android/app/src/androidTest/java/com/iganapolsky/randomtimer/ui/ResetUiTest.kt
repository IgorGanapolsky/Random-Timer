package com.iganapolsky.randomtimer.ui

import android.Manifest
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.rule.GrantPermissionRule
import com.iganapolsky.randomtimer.MainActivity
import org.junit.Rule
import org.junit.Test
import org.junit.rules.RuleChain
import org.junit.rules.TestRule
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ResetUiTest {
    private val permissionRule = GrantPermissionRule.grant(
        Manifest.permission.POST_NOTIFICATIONS
    )

    private val composeRule = createAndroidComposeRule<MainActivity>()

    @get:Rule
    val ruleChain: TestRule = RuleChain.outerRule(permissionRule).around(composeRule)

    @Test
    fun resetShowsRestartedFeedback() {
        if (composeRule.onAllNodesWithText("Start Timer").fetchSemanticsNodes().isEmpty()) {
            if (composeRule.onAllNodesWithText("Stop").fetchSemanticsNodes().isNotEmpty()) {
                composeRule.onNodeWithText("Stop").performClick()
            }
        }
        composeRule.waitUntil(timeoutMillis = 2000) {
            composeRule.onAllNodesWithText("Start Timer")
                .fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithText("Start Timer")
            .assertExists()
            .performClick()

        composeRule.onNodeWithText("Timer running...")
            .assertExists()

        composeRule.onNodeWithText("Reset")
            .assertExists()
            .performClick()

        composeRule.waitUntil(timeoutMillis = 2000) {
            composeRule.onAllNodesWithText("Timer restarted")
                .fetchSemanticsNodes().isNotEmpty()
        }
    }
}
