package com.iganapolsky.randomtimer.ui

import android.content.Intent
import androidx.compose.ui.test.junit4.AndroidComposeTestRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.platform.app.InstrumentationRegistry
import com.iganapolsky.randomtimer.MainActivity
import com.iganapolsky.randomtimer.service.TimerForegroundService
import org.junit.rules.ExternalResource

/** Shared helpers for slow GitHub Actions emulators (API 30, swiftshader). */
object DeviceTestSupport {
    const val SETUP_READY_TIMEOUT_MS = 30_000L

    /** Stops process + foreground timer so the next MainActivity lands on setup. */
    fun forceStopApp() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.uiAutomation.executeShellCommand(
            "am force-stop com.iganapolsky.randomtimer",
        )
    }

    fun stopTimerService() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val stopIntent =
            Intent(context, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_STOP
            }
        context.startService(stopIntent)
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

/** Runs before [androidx.compose.ui.test.junit4.createAndroidComposeRule] launches MainActivity. */
class ForceStopBeforeMainActivityRule : ExternalResource() {
    override fun before() {
        DeviceTestSupport.stopTimerService()
        DeviceTestSupport.forceStopApp()
    }
}
