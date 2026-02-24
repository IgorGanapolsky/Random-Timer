package com.iganapolsky.randomtimer

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.notifications.ReengagementScheduler
import com.iganapolsky.randomtimer.service.TimerForegroundService
import com.iganapolsky.randomtimer.ui.navigation.RandomTimerNavHost
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    @Inject lateinit var analyticsService: AnalyticsService

    private val notificationPermissionLauncher =
        registerForActivityResult(
            ActivityResultContracts.RequestPermission(),
        ) { isGranted ->
            // Handle permission result if needed
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Show timer UI over lock screen (like Samsung Clock)
        setShowWhenLocked(true)
        setTurnScreenOn(true)

        enableEdgeToEdge()
        requestNotificationPermission()
        handleAlarmNotificationTap(intent)
        handleDeepLink(intent)

        // User is back — cancel any pending re-engagement reminders
        ReengagementScheduler.cancel(this)

        setContent {
            RandomTimerTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = TimerColors.BackgroundDark,
                ) {
                    RandomTimerNavHost()
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleAlarmNotificationTap(intent)
        handleDeepLink(intent)
    }

    override fun onResume() {
        super.onResume()
        // Tell service app is in foreground - suppress notifications
        sendAppStateToService(isInForeground = true)
    }

    override fun onPause() {
        super.onPause()
        // Tell service app is in background - show notifications
        sendAppStateToService(isInForeground = false)
    }

    private fun handleAlarmNotificationTap(intent: Intent?) {
        if (intent?.getBooleanExtra(TimerForegroundService.EXTRA_FROM_ALARM_NOTIFICATION, false) == true) {
            // User tapped the alarm notification — stop sound/vibration but keep alarm screen.
            // The alarm screen shows because timerState.status == ALARM.
            val silenceIntent =
                Intent(this, TimerForegroundService::class.java).apply {
                    action = TimerForegroundService.ACTION_SILENCE_ALARM
                }
            startService(silenceIntent)
            intent.removeExtra(TimerForegroundService.EXTRA_FROM_ALARM_NOTIFICATION)
        }

        if (intent?.getBooleanExtra(TimerForegroundService.EXTRA_FROM_ALARM_STOP_ACTION, false) == true) {
            // User tapped the alarm notification Stop action — dismiss alarm and go home.
            val dismissIntent =
                Intent(this, TimerForegroundService::class.java).apply {
                    action = TimerForegroundService.ACTION_DISMISS_ALARM
                }
            startService(dismissIntent)
            intent.removeExtra(TimerForegroundService.EXTRA_FROM_ALARM_STOP_ACTION)
        }
    }

    private fun sendAppStateToService(isInForeground: Boolean) {
        val intent =
            Intent(this, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_APP_STATE_CHANGED
                putExtra(TimerForegroundService.EXTRA_APP_IN_FOREGROUND, isInForeground)
            }
        startService(intent)
    }

    private fun handleDeepLink(intent: Intent?) {
        val uri = intent?.data ?: return
        analyticsService.trackDeepLink(uri)
    }

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(
                    this,
                    Manifest.permission.POST_NOTIFICATIONS,
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }
}
