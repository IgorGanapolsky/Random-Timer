package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.By
import androidx.test.uiautomator.UiDevice
import androidx.test.uiautomator.Until
import com.iganapolsky.randomtimer.MainActivity
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NotificationE2ETest {

    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    private lateinit var device: UiDevice

    @Before
    fun setup() {
        device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
    }

    @Test
    fun testNotificationLifecycle() {
        // 1. Start a timer from the UI
        composeRule.waitUntil(timeoutMillis = 5_000) {
            composeRule
                .onAllNodesWithText("Start First Drill")
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
        
        composeRule.onNodeWithText("Start First Drill").performClick()

        // 2. Background the app to show notification
        device.pressHome()

        // 3. Open notification shade
        device.openNotification()
        
        // 4. Verify notification is visible
        val notificationTitle = device.wait(Until.findObject(By.text("Timer Running")), 5000)
        assertNotNull("Notification with title 'Timer Running' should be visible", notificationTitle)

        // 5. Click 'Pause'
        val pauseButton = device.findObject(By.text("Pause"))
        assertNotNull("Pause button should be visible", pauseButton)
        pauseButton.click()

        // 6. Verify title changes to 'Timer Paused'
        val pausedTitle = device.wait(Until.findObject(By.text("Timer Paused")), 5000)
        assertNotNull("Notification title should change to 'Timer Paused'", pausedTitle)

        // 7. Click 'Resume'
        val resumeButton = device.findObject(By.text("Resume"))
        assertNotNull("Resume button should be visible", resumeButton)
        resumeButton.click()
        
        // 8. Verify title changes back to 'Timer Running'
        val runningTitle = device.wait(Until.findObject(By.text("Timer Running")), 5000)
        assertNotNull("Notification title should change back to 'Timer Running'", runningTitle)

        // 9. Click 'Stop'
        val stopButton = device.findObject(By.text("Stop"))
        assertNotNull("Stop button should be visible", stopButton)
        stopButton.click()

        // 10. Verify notification is dismissed
        val dismissed = device.wait(Until.gone(By.text("Timer Running")), 5000)
        assertTrue("Notification should be dismissed after clicking 'Stop'", dismissed)
        
        device.pressHome()
    }

    @Test
    fun testExtendTimerAction() {
        // 1. Start a timer
        composeRule.waitUntil(timeoutMillis = 5_000) {
            composeRule.onAllNodesWithText("Start First Drill").fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("Start First Drill").performClick()

        // 2. Open notification
        device.pressHome()
        device.openNotification()

        // 3. Verify '+5 Min' button exists
        val extendButton = device.findObject(By.text("+5 Min"))
        assertNotNull("'+5 Min' button should be visible", extendButton)

        // 4. Click '+5 Min'
        extendButton.click()
        
        // 5. Verify notification still shows 'Timer Running' (it shouldn't disappear)
        val runningTitle = device.wait(Until.findObject(By.text("Timer Running")), 2000)
        assertNotNull("Notification should still be visible after extend", runningTitle)

        // 6. Stop and cleanup
        device.findObject(By.text("Stop")).click()
        device.pressHome()
    }
}
