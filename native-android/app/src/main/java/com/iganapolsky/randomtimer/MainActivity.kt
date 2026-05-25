package com.iganapolsky.randomtimer

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.KeyEvent
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import com.iganapolsky.randomtimer.BuildConfig
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.notifications.MonthlyContentWorker
import com.iganapolsky.randomtimer.notifications.ReengagementScheduler
import com.iganapolsky.randomtimer.service.MediaButtonHandler
import com.iganapolsky.randomtimer.service.TimerForegroundService
import com.iganapolsky.randomtimer.ui.navigation.RandomTimerNavHost
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import com.iganapolsky.randomtimer.updates.InAppUpdateManager
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    @Inject lateinit var analyticsService: AnalyticsService
    @Inject lateinit var inAppUpdateManager: InAppUpdateManager
    private var latestDeepLinkUri by mutableStateOf<Uri?>(null)

    private val notificationPermissionLauncher =
        registerForActivityResult(
            ActivityResultContracts.RequestPermission(),
        ) { isGranted ->
            // Handle permission result if needed
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Show timer UI over lock screen (like Samsung Clock)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        }

        enableEdgeToEdge()
        requestNotificationPermission()
        handleAlarmNotificationTap(intent)
        latestDeepLinkUri = handleDeepLink(intent)

        inAppUpdateManager.checkForUpdates(this)
        MonthlyContentWorker.schedule(this)

        // User is back — cancel any pending re-engagement reminders
        ReengagementScheduler.cancel(this)

        setContent {
            RandomTimerTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = TimerColors.BackgroundDark,
                ) {
                    RandomTimerNavHost(pendingDeepLinkUri = latestDeepLinkUri?.toString())
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleAlarmNotificationTap(intent)
        latestDeepLinkUri = null
        latestDeepLinkUri = handleDeepLink(intent)
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

    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        if (MediaButtonHandler.isVolumeKey(event.keyCode) &&
            MediaButtonHandler.shouldSilenceAlarm(event.keyCode, event.action)
        ) {
            silenceAlarmFromVolumeKey()
        }
        return super.dispatchKeyEvent(event)
    }

    private fun silenceAlarmFromVolumeKey() {
        val silenceIntent =
            Intent(this, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_SILENCE_ALARM
            }
        startService(silenceIntent)
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

    private fun handleDeepLink(intent: Intent?): Uri? {
        val uri = intent?.data ?: return null
        analyticsService.trackDeepLink(uri)
        return uri
    }

    private fun requestNotificationPermission() {
        // Debug builds on AVD: runtime permission sheet can block Maestro from seeing Compose targets.
        if (BuildConfig.DEBUG && isGenericAndroidEmulator()) {
            return
        }
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

    private fun isGenericAndroidEmulator(): Boolean {
        val fp = Build.FINGERPRINT.lowercase()
        val model = Build.MODEL.lowercase()
        val product = Build.PRODUCT.lowercase()
        return fp.contains("emulator") ||
            fp.startsWith("generic") ||
            model.contains("sdk_gphone") ||
            model.contains("emulator") ||
            product.contains("sdk_gphone") ||
            product.contains("emulator")
    }
}
