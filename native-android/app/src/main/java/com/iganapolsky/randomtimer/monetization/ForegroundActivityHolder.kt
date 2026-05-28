package com.iganapolsky.randomtimer.monetization

import android.app.Activity
import java.lang.ref.WeakReference

/** Tracks the foreground activity for AdMob rewarded presentation. */
object ForegroundActivityHolder {
    private var activityRef: WeakReference<Activity>? = null

    fun setActivity(activity: Activity?) {
        activityRef = activity?.let { WeakReference(it) }
    }

    fun getActivity(): Activity? = activityRef?.get()
}
