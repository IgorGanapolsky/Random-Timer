package com.iganapolsky.randomtimer.notifications

import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import com.iganapolsky.randomtimer.MainActivity
import com.iganapolsky.randomtimer.R

class ReengagementReceiver : BroadcastReceiver() {
    override fun onReceive(
        context: Context,
        intent: Intent,
    ) {
        val channelId = "reengagement"
        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel =
                NotificationChannel(
                    channelId,
                    "Training Reminders",
                    NotificationManager.IMPORTANCE_DEFAULT,
                )
            nm.createNotificationChannel(channel)
        }

        val title = intent.getStringExtra("title") ?: "Keep your streak alive"
        val body = intent.getStringExtra("body") ?: "Train for chaos, not comfort."

        val openIntent =
            Intent(context, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
        val pendingIntent =
            PendingIntent.getActivity(
                context,
                0,
                openIntent,
                PendingIntent.FLAG_IMMUTABLE,
            )

        val notification =
            NotificationCompat
                .Builder(context, channelId)
                .setSmallIcon(R.drawable.ic_timer)
                .setContentTitle(title)
                .setContentText(body)
                .setContentIntent(pendingIntent)
                .setAutoCancel(true)
                .build()

        nm.notify(intent.getIntExtra("id", 1001), notification)
        Log.d("ReengagementScheduler", "Delivered re-engagement notification: $title")
    }
}

object ReengagementScheduler {
    private const val TAG = "ReengagementScheduler"

    fun schedule(context: Context) {
        cancel(context)
        val am = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager

        // 24h reminder
        scheduleOne(
            context,
            am,
            24 * 3600 * 1000L,
            1001,
            "Keep your streak alive",
            "Train for chaos, not comfort. Your next random drill is waiting.",
        )
        // 72h reminder
        scheduleOne(
            context,
            am,
            72 * 3600 * 1000L,
            1002,
            "Don't break the habit",
            "Fighters train when they don't feel like it. Open Random Tactical Timer.",
        )
        Log.d(TAG, "Scheduled re-engagement reminders at 24h and 72h")
    }

    fun cancel(context: Context) {
        val am = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        for (id in listOf(1001, 1002)) {
            val intent = Intent(context, ReengagementReceiver::class.java)
            val pi =
                PendingIntent.getBroadcast(
                    context,
                    id,
                    intent,
                    PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_NO_CREATE,
                )
            pi?.let {
                am.cancel(it)
                Log.d(TAG, "Cancelled re-engagement alarm id=$id")
            }
        }
    }

    private fun scheduleOne(
        context: Context,
        am: AlarmManager,
        delayMs: Long,
        id: Int,
        title: String,
        body: String,
    ) {
        val intent =
            Intent(context, ReengagementReceiver::class.java).apply {
                putExtra("id", id)
                putExtra("title", title)
                putExtra("body", body)
            }
        val pi =
            PendingIntent.getBroadcast(
                context,
                id,
                intent,
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
            )
        am.set(AlarmManager.RTC_WAKEUP, System.currentTimeMillis() + delayMs, pi)
    }
}
