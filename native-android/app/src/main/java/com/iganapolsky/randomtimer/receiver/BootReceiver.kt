package com.iganapolsky.randomtimer.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Restores active timer after device reboot.
 */
@AndroidEntryPoint
class BootReceiver : BroadcastReceiver() {

    @Inject
    lateinit var timerRepository: TimerRepository

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED) return

        val pendingResult = goAsync()

        scope.launch {
            try {
                // Check if there was an active timer
                val activeTimer = timerRepository.getActiveTimer().first()

                if (activeTimer != null) {
                    // Calculate how much time has passed since boot
                    // and resume/complete the timer accordingly
                    val elapsed = System.currentTimeMillis() - activeTimer.startedAt
                    val elapsedDuration = kotlin.time.Duration.parse("${elapsed}ms")

                    if (elapsedDuration >= activeTimer.targetDuration) {
                        // Timer should have completed - trigger alarm
                        // TODO: Start service with alarm state
                    } else {
                        // Timer still running - resume
                        // TODO: Start service with remaining time
                    }
                }
            } finally {
                pendingResult.finish()
            }
        }
    }
}
