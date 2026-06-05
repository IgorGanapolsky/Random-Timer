package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.test.junit4.AndroidComposeTestRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.platform.app.InstrumentationRegistry
import com.iganapolsky.randomtimer.MainActivity

/** Shared helpers for slow GitHub Actions emulators (API 30, swiftshader). */
object DeviceTestSupport {
    const val SETUP_READY_TIMEOUT_MS = 30_000L

    fun clearAppData() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.uiAutomation.executeShellCommand(
            "pm clear com.iganapolsky.randomtimer",
        )
    }

    fun waitForSetupScreen(
        rule: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>,
        timeoutMillis: Long = SETUP_READY_TIMEOUT_MS,
    ) {
        rule.waitUntil(timeoutMillis = timeoutMillis) {
            rule.onAllNodesWithTag("start_timer", useUnmergedTree = true)
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
        rule.waitForIdle()
    }

    fun clickPrimaryStart(
        rule: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>,
    ) {
        rule.onNodeWithTag("start_timer", useUnmergedTree = true).performClick()
    }
}
