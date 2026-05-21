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
import com.iganapolsky.randomtimer.billing.ProEntitlementSnapshot
import java.util.Calendar
import java.util.concurrent.TimeUnit

class MonthlyContentWorker(
    context: Context,
    params: WorkerParameters,
    private val calendarProvider: () -> Calendar = { Calendar.getInstance() },
    private val isProProvider: () -> Boolean = { ProEntitlementSnapshot.readIsPro(context) },
    private val releaseMonthProvider: () -> String? = { ProMonthlyManifestReader.fetchReleaseMonth() },
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        if (!isProProvider()) {
            return Result.success()
        }

        val calendar = calendarProvider()
        if (calendar.get(Calendar.DAY_OF_MONTH) != 1) {
            return Result.success()
        }

        val releaseMonth = releaseMonthProvider() ?: return Result.success()
        showMonthlyNotification(releaseMonth)
        return Result.success()
    }

    private fun showMonthlyNotification(releaseMonth: String) {
        val copy = ProMonthlyContentMessaging.notificationCopy(releaseMonth)
        val channelId = "monthly_content"
        val nm = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel =
                NotificationChannel(
                    channelId,
                    "New Content Alerts",
                    NotificationManager.IMPORTANCE_HIGH,
                )
            nm.createNotificationChannel(channel)
        }

        val openIntent =
            Intent(applicationContext, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
        val pendingIntent =
            PendingIntent.getActivity(
                applicationContext,
                0,
                openIntent,
                PendingIntent.FLAG_IMMUTABLE,
            )

        val notification =
            NotificationCompat
                .Builder(applicationContext, channelId)
                .setSmallIcon(R.drawable.ic_timer)
                .setContentTitle(copy.title)
                .setContentText(copy.body)
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setContentIntent(pendingIntent)
                .setAutoCancel(true)
                .build()

        nm.notify(NOTIFICATION_ID, notification)
    }

    companion object {
        const val NOTIFICATION_ID = 2001
        private const val WORK_NAME = "MonthlyContentWorker"

        fun schedule(context: Context) {
            val workRequest =
                PeriodicWorkRequestBuilder<MonthlyContentWorker>(
                    1,
                    TimeUnit.DAYS,
                ).build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                workRequest,
            )
        }
    }
}
