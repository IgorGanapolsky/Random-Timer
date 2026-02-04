package com.iganapolsky.randomtimer.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.iganapolsky.randomtimer.service.TimerForegroundService
import dagger.hilt.android.AndroidEntryPoint

/**
 * Receives exact alarm broadcasts and triggers the alarm notification/sound.
 * Used with AlarmManager for precise timing even in Doze mode.
 */
@AndroidEntryPoint
class AlarmReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            ACTION_ALARM_TRIGGER -> {
                // The foreground service handles the actual alarm
                // This receiver is for backup/edge cases where the service might have been killed
                val serviceIntent = Intent(context, TimerForegroundService::class.java).apply {
                    action = TimerForegroundService.ACTION_DISMISS_ALARM
                }
                context.startService(serviceIntent)
            }
        }
    }

    companion object {
        const val ACTION_ALARM_TRIGGER = "com.iganapolsky.randomtimer.ALARM_TRIGGER"
    }
}
