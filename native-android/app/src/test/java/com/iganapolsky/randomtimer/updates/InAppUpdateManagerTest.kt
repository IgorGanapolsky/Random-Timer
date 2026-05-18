package com.iganapolsky.randomtimer.updates

import android.app.Activity
import com.google.android.gms.tasks.OnSuccessListener
import com.google.android.gms.tasks.Task
import com.google.android.play.core.appupdate.AppUpdateInfo
import com.google.android.play.core.appupdate.AppUpdateManager
import com.google.android.play.core.install.model.AppUpdateType
import com.google.android.play.core.install.model.UpdateAvailability
import io.mockk.every
import io.mockk.mockk
import io.mockk.slot
import io.mockk.verify
import org.junit.Before
import org.junit.Test

class InAppUpdateManagerTest {

    private lateinit var appUpdateManager: AppUpdateManager
    private lateinit var inAppUpdateManager: InAppUpdateManager
    private val activity = mockk<Activity>(relaxed = true)

    @Before
    fun setup() {
        appUpdateManager = mockk(relaxed = true)
        inAppUpdateManager = InAppUpdateManager(appUpdateManager)
    }

    @Test
    fun `checkForUpdates triggers immediate update when priority is high`() {
        val appUpdateInfo = mockk<AppUpdateInfo> {
            every { updateAvailability() } returns UpdateAvailability.UPDATE_AVAILABLE
            every { updatePriority() } returns 5
            every { isUpdateTypeAllowed(AppUpdateType.IMMEDIATE) } returns true
        }

        val task = mockk<Task<AppUpdateInfo>>()
        val slot = slot<OnSuccessListener<AppUpdateInfo>>()
        
        every { appUpdateManager.appUpdateInfo } returns task
        every { task.addOnSuccessListener(capture(slot)) } returns task

        inAppUpdateManager.checkForUpdates(activity)

        // Simulate success
        slot.captured.onSuccess(appUpdateInfo)

        verify {
            appUpdateManager.startUpdateFlowForResult(
                appUpdateInfo,
                activity,
                any(),
                InAppUpdateManager.UPDATE_REQUEST_CODE
            )
        }
    }

    @Test
    fun `checkForUpdates triggers flexible update when priority is low`() {
        val appUpdateInfo = mockk<AppUpdateInfo> {
            every { updateAvailability() } returns UpdateAvailability.UPDATE_AVAILABLE
            every { updatePriority() } returns 2
            every { isUpdateTypeAllowed(AppUpdateType.FLEXIBLE) } returns true
        }

        val task = mockk<Task<AppUpdateInfo>>()
        val slot = slot<OnSuccessListener<AppUpdateInfo>>()
        
        every { appUpdateManager.appUpdateInfo } returns task
        every { task.addOnSuccessListener(capture(slot)) } returns task

        inAppUpdateManager.checkForUpdates(activity)

        // Simulate success
        slot.captured.onSuccess(appUpdateInfo)

        verify {
            appUpdateManager.startUpdateFlowForResult(
                appUpdateInfo,
                activity,
                any(),
                InAppUpdateManager.UPDATE_REQUEST_CODE
            )
        }
    }
}
