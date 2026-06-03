package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.test.junit4.createAndroidComposeRule
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
        DeviceTestSupport.clearAppData()
        device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
    }

    @Test
    fun testNotificationLifecycle() {
        DeviceTestSupport.waitForSetupScreen(composeRule)
        DeviceTestSupport.clickPrimaryStart(composeRule)

        device.pressHome()
        device.openNotification()

        val notificationTitle = device.wait(Until.findObject(By.text("Timer Running")), 5000)
        assertNotNull("Notification with title 'Timer Running' should be visible", notificationTitle)

        val pauseButton = device.findObject(By.text("Pause"))
        assertNotNull("Pause button should be visible", pauseButton)
        pauseButton.click()

        val pausedTitle = device.wait(Until.findObject(By.text("Timer Paused")), 5000)
        assertNotNull("Notification title should change to 'Timer Paused'", pausedTitle)

        val resumeButton = device.findObject(By.text("Resume"))
        assertNotNull("Resume button should be visible", resumeButton)
        resumeButton.click()

        val runningTitle = device.wait(Until.findObject(By.text("Timer Running")), 5000)
        assertNotNull("Notification title should change back to 'Timer Running'", runningTitle)

        val stopButton = device.findObject(By.text("Stop"))
        assertNotNull("Stop button should be visible", stopButton)
        stopButton.click()

        val dismissed = device.wait(Until.gone(By.text("Timer Running")), 5000)
        assertTrue("Notification should be dismissed after clicking 'Stop'", dismissed)

        device.pressHome()
    }

    @Test
    fun testExtendTimerAction() {
        DeviceTestSupport.waitForSetupScreen(composeRule)
        DeviceTestSupport.clickPrimaryStart(composeRule)

        device.pressHome()
        device.openNotification()

        val extendButton = device.findObject(By.text("+5 Min"))
        assertNotNull("'+5 Min' button should be visible", extendButton)
        extendButton.click()

        val runningTitle = device.wait(Until.findObject(By.text("Timer Running")), 2000)
        assertNotNull("Notification should still be visible after extend", runningTitle)

        device.findObject(By.text("Stop")).click()
        device.pressHome()
    }
}
