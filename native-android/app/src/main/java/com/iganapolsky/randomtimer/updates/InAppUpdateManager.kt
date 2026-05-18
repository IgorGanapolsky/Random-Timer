package com.iganapolsky.randomtimer.updates

import android.app.Activity
import android.content.Context
import android.util.Log
import com.google.android.play.core.appupdate.AppUpdateManager
import com.google.android.play.core.appupdate.AppUpdateManagerFactory
import com.google.android.play.core.appupdate.AppUpdateOptions
import com.google.android.play.core.install.model.AppUpdateType
import com.google.android.play.core.install.model.UpdateAvailability
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class InAppUpdateManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val appUpdateManager: AppUpdateManager = AppUpdateManagerFactory.create(context)

    companion object {
        private const val TAG = "InAppUpdateManager"
        const val UPDATE_REQUEST_CODE = 1234
    }

    /**
     * Checks for available updates and triggers the appropriate flow.
     * @param activity The activity from which to launch the update flow.
     */
    fun checkForUpdates(activity: Activity) {
        val appUpdateInfoTask = appUpdateManager.appUpdateInfo

        appUpdateInfoTask.addOnSuccessListener { appUpdateInfo ->
            if (appUpdateInfo.updateAvailability() == UpdateAvailability.UPDATE_AVAILABLE) {
                // Priority evaluation: 0-5. 
                // 5: Immediate (Force), 4: Immediate (Recommended), 1-3: Flexible
                val priority = appUpdateInfo.updatePriority()
                Log.d(TAG, "Update available with priority: $priority")

                if (priority >= 4 && appUpdateInfo.isUpdateTypeAllowed(AppUpdateType.IMMEDIATE)) {
                    triggerImmediateUpdate(activity, appUpdateManager)
                } else if (appUpdateInfo.isUpdateTypeAllowed(AppUpdateType.FLEXIBLE)) {
                    triggerFlexibleUpdate(activity, appUpdateManager)
                }
            } else if (appUpdateInfo.updateAvailability() == UpdateAvailability.DEVELOPER_TRIGGERED_UPDATE_IN_PROGRESS) {
                // Resume an update already in progress
                triggerImmediateUpdate(activity, appUpdateManager)
            }
        }
    }

    private fun triggerImmediateUpdate(activity: Activity, manager: AppUpdateManager) {
        val infoTask = manager.appUpdateInfo
        infoTask.addOnSuccessListener { info ->
            manager.startUpdateFlowForResult(
                info,
                activity,
                AppUpdateOptions.defaultOptions(AppUpdateType.IMMEDIATE),
                UPDATE_REQUEST_CODE
            )
        }
    }

    private fun triggerFlexibleUpdate(activity: Activity, manager: AppUpdateManager) {
        val infoTask = manager.appUpdateInfo
        infoTask.addOnSuccessListener { info ->
            manager.startUpdateFlowForResult(
                info,
                activity,
                AppUpdateOptions.defaultOptions(AppUpdateType.FLEXIBLE),
                UPDATE_REQUEST_CODE
            )
        }
    }
}
