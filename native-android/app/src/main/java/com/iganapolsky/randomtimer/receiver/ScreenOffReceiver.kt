package com.iganapolsky.randomtimer.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * Silences the alarm when the screen turns off (e.g. power button press).
 *
 * Must be registered programmatically — ACTION_SCREEN_OFF cannot be declared
 * in the manifest.
 */
class ScreenOffReceiver(private val onScreenOff: () -> Unit) : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_SCREEN_OFF) {
            onScreenOff()
        }
    }
}
