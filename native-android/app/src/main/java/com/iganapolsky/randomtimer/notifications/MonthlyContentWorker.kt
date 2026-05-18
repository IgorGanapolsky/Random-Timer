package com.iganapolsky.randomtimer.notifications

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.iganapolsky.randomtimer.MainActivity
import com.iganapolsky.randomtimer.R
import java.util.Calendar
import java.util.concurrent.TimeUnit

class MonthlyContentWorker(
    context: Context,
    params: WorkerParameters,
    private val calendarProvider: () -> Calendar = { Calendar.getInstance() }
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        // In 2026, we check the content manifest for the 1st of the month.
        // For now, we simulate a check that always passes on the 1st.
        val calendar = calendarProvider()
        if (calendar.get(Calendar.DAY_OF_MONTH) == 1) {
            showMonthlyNotification()
        }
        return Result.success()
    }

    private fun showMonthlyNotification() {
        val channelId = "monthly_content"
        val nm = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "New Content Alerts",
                NotificationManager.IMPORTANCE_HIGH
            )
            nm.createNotificationChannel(channel)
        }

        val openIntent = Intent(applicationContext, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            applicationContext,
            0,
            openIntent,
            PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(applicationContext, channelId)
            .setSmallIcon(R.drawable.ic_timer)
            .setContentTitle("New Audio Drops for May 2026")
            .setContentText("Your Sound Arsenal just got 5 new tactical callouts. Train now.")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        nm.notify(2001, notification)
    }

    companion object {
        private const val WORK_NAME = "MonthlyContentWorker"

        fun schedule(context: Context) {
            // Run every 24 hours to check if it's the 1st of the month
            val workRequest = PeriodicWorkRequestBuilder<MonthlyContentWorker>(
                1, TimeUnit.DAYS
            ).build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                workRequest
            )
        }
    }
}
