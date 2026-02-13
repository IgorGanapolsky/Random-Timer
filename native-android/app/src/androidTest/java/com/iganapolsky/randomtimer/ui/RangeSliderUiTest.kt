package com.iganapolsky.randomtimer.ui

import android.Manifest
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performSemanticsAction
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.rule.GrantPermissionRule
import com.iganapolsky.randomtimer.MainActivity
import org.junit.Rule
import org.junit.Test
import org.junit.rules.RuleChain
import org.junit.rules.TestRule
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class RangeSliderUiTest {
    private val permissionRule = GrantPermissionRule.grant(
        Manifest.permission.POST_NOTIFICATIONS
    )

    private val composeRule = createAndroidComposeRule<MainActivity>()

    @get:Rule
    val ruleChain: TestRule = RuleChain.outerRule(permissionRule).around(composeRule)

    @Test
    fun draggingMinBeyondGapPushesMaxForward() {
        // Reduce max to 60s.
        composeRule.onNodeWithContentDescription("Maximum time slider")
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(60f)
            }
        composeRule.waitForIdle()
        composeRule.onNodeWithText("Maximum: 1m").assertExists()

        // Move min close to max; max should be pushed to keep a 30s gap.
        composeRule.onNodeWithContentDescription("Minimum time slider")
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(50f)
            }
        composeRule.waitForIdle()
        composeRule.onNodeWithText("Minimum: 50s").assertExists()
        composeRule.onNodeWithText("Maximum: 1m 20s").assertExists()
    }

    @Test
    fun draggingMaxBelowGapPullsMinBack() {
        // Set min to 150s (2m 30s). Max is still 5m so this should not push max.
        composeRule.onNodeWithContentDescription("Minimum time slider")
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(150f)
            }
        composeRule.waitForIdle()
        composeRule.onNodeWithText("Minimum: 2m 30s").assertExists()

        // Move max below min + 30s; min should be pulled back.
        composeRule.onNodeWithContentDescription("Maximum time slider")
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress ->
                setProgress(160f)
            }
        composeRule.waitForIdle()
        composeRule.onNodeWithText("Maximum: 2m 40s").assertExists()
        composeRule.onNodeWithText("Minimum: 2m 10s").assertExists()
    }
}

