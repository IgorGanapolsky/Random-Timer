package com.iganapolsky.randomtimer.updates

import android.app.Activity
import android.util.Log
import com.google.android.play.core.appupdate.AppUpdateInfo
import com.google.android.play.core.appupdate.AppUpdateManager
import com.google.android.play.core.appupdate.AppUpdateOptions
import com.google.android.play.core.install.model.AppUpdateType
import com.google.android.play.core.install.model.UpdateAvailability
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class InAppUpdateManager @Inject constructor(
    private val appUpdateManager: AppUpdateManager
) {
    companion object {
        private const val TAG = "InAppUpdateManager"
        const val UPDATE_REQUEST_CODE = 1234
    }

    /**
     * Checks for available updates and triggers the appropriate flow.
     * @param activity The activity from which to launch the update flow.
     */
    fun checkForUpdates(activity: Activity) {
        appUpdateManager.appUpdateInfo.addOnSuccessListener { appUpdateInfo ->
            if (appUpdateInfo.updateAvailability() == UpdateAvailability.UPDATE_AVAILABLE) {
                // Priority evaluation: 0-5. 
                // 5: Immediate (Force), 4: Immediate (Recommended), 1-3: Flexible
                val priority = appUpdateInfo.updatePriority()
                Log.d(TAG, "Update available with priority: $priority")

                if (priority >= 4 && appUpdateInfo.isUpdateTypeAllowed(AppUpdateType.IMMEDIATE)) {
                    triggerUpdate(activity, appUpdateInfo, AppUpdateType.IMMEDIATE)
                } else if (appUpdateInfo.isUpdateTypeAllowed(AppUpdateType.FLEXIBLE)) {
                    triggerUpdate(activity, appUpdateInfo, AppUpdateType.FLEXIBLE)
                }
            } else if (appUpdateInfo.updateAvailability() == UpdateAvailability.DEVELOPER_TRIGGERED_UPDATE_IN_PROGRESS) {
                // Resume an update already in progress
                triggerUpdate(activity, appUpdateInfo, AppUpdateType.IMMEDIATE)
            }
        }
    }

    private fun triggerUpdate(activity: Activity, info: AppUpdateInfo, type: Int) {
        appUpdateManager.startUpdateFlowForResult(
            info,
            activity,
            AppUpdateOptions.defaultOptions(type),
            UPDATE_REQUEST_CODE
        )
    }
}
