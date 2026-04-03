package com.iganapolsky.randomtimer.ui

import android.Manifest
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.rule.GrantPermissionRule
import com.iganapolsky.randomtimer.MainActivity
import org.junit.Rule
import org.junit.Test
import org.junit.rules.RuleChain
import org.junit.rules.TestRule
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class TimerSetupSmokeTest {
    private val permissionRule =
        GrantPermissionRule.grant(
            Manifest.permission.POST_NOTIFICATIONS,
        )

    private val composeRule = createAndroidComposeRule<MainActivity>()

    @get:Rule
    val ruleChain: TestRule = RuleChain.outerRule(permissionRule).around(composeRule)

    @Test
    fun setupScreenRendersCoreControls() {
        composeRule.waitUntil(timeoutMillis = 5_000) {
            composeRule
                .onAllNodesWithText("Start Timer")
                .fetchSemanticsNodes()
                .isNotEmpty()
        }

        composeRule
            .onNodeWithText("Start Timer")
            .assertExists()

        composeRule
            .onNodeWithContentDescription("Minimum time slider")
            .assertExists()

        composeRule
            .onNodeWithContentDescription("Maximum time slider")
            .assertExists()
    }
}
