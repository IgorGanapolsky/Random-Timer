package com.iganapolsky.randomtimer.service

import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import com.iganapolsky.randomtimer.domain.model.TimerState
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TimerServiceControllerImpl @Inject constructor(
    @ApplicationContext private val context: Context
) : TimerServiceController {

    override fun bindService(connection: ServiceConnection) {
        val intent = Intent(context, TimerForegroundService::class.java)
        context.bindService(intent, connection, Context.BIND_AUTO_CREATE)
    }

    override fun unbindService(connection: ServiceConnection) {
        context.unbindService(connection)
    }

    override fun startTimer(state: TimerState) {
        val intent = Intent(context, TimerForegroundService::class.java).apply {
            action = TimerForegroundService.ACTION_START
            putExtra(TimerForegroundService.EXTRA_APP_IN_FOREGROUND, true)
            putExtra(TimerForegroundService.EXTRA_TARGET_DURATION_MS, state.targetDuration.inWholeMilliseconds)
            putExtra(TimerForegroundService.EXTRA_REMAINING_DURATION_MS, state.remainingDuration.inWholeMilliseconds)
            putExtra(TimerForegroundService.EXTRA_MIN_SECONDS, state.config.minSeconds)
            putExtra(TimerForegroundService.EXTRA_MAX_SECONDS, state.config.maxSeconds)
            putExtra(TimerForegroundService.EXTRA_ALARM_DURATION, state.config.alarmDuration)
            putExtra(TimerForegroundService.EXTRA_HIDDEN_MODE, state.config.hiddenMode)
            putExtra(TimerForegroundService.EXTRA_REPEAT_ENABLED, state.config.repeatEnabled)
            putExtra(TimerForegroundService.EXTRA_SOUND_TYPE, state.config.soundType.name)
            putExtra(TimerForegroundService.EXTRA_VOLUME, state.config.volume)
            putExtra(TimerForegroundService.EXTRA_VIBRATION_ENABLED, state.config.vibrationEnabled)
            putExtra(TimerForegroundService.EXTRA_USE_EXTENDED_RANGE, state.config.useExtendedRange)
            putExtra(TimerForegroundService.EXTRA_VOICE_ENABLED, state.config.voiceEnabled)
            putExtra(TimerForegroundService.EXTRA_REPEAT_ROUNDS, state.config.repeatRounds)
            putExtra(TimerForegroundService.EXTRA_ROUND_COUNT, state.roundCount)
        }

        override fun unbindService(connection: ServiceConnection) {
            context.unbindService(connection)
        }

        override fun startTimer(state: TimerState) {
            val intent =
                Intent(context, TimerForegroundService::class.java).apply {
                    action = TimerForegroundService.ACTION_START
                    putExtra(TimerForegroundService.EXTRA_APP_IN_FOREGROUND, true)
                    putExtra(TimerForegroundService.EXTRA_TARGET_DURATION_MS, state.targetDuration.inWholeMilliseconds)
                    putExtra(TimerForegroundService.EXTRA_REMAINING_DURATION_MS, state.remainingDuration.inWholeMilliseconds)
                    putExtra(TimerForegroundService.EXTRA_MIN_SECONDS, state.config.minSeconds)
                    putExtra(TimerForegroundService.EXTRA_MAX_SECONDS, state.config.maxSeconds)
                    putExtra(TimerForegroundService.EXTRA_ALARM_DURATION, state.config.alarmDuration)
                    putExtra(TimerForegroundService.EXTRA_HIDDEN_MODE, state.config.hiddenMode)
                    putExtra(TimerForegroundService.EXTRA_REPEAT_ENABLED, state.config.repeatEnabled)
                    putExtra(TimerForegroundService.EXTRA_SOUND_TYPE, state.config.soundType.name)
                    putExtra(TimerForegroundService.EXTRA_VOLUME, state.config.volume)
                    putExtra(TimerForegroundService.EXTRA_VIBRATION_ENABLED, state.config.vibrationEnabled)
                    putExtra(TimerForegroundService.EXTRA_VOICE_CALLOUTS_ENABLED, state.config.voiceCalloutsEnabled)
                }
            // Timer starts from the foreground UI, so a regular service start avoids forcing
            // an immediate foreground notification while the app is visible.
            context.startService(intent)
        }

        override fun stopTimer() {
            sendAction(TimerForegroundService.ACTION_STOP)
        }

        override fun dismissAlarm() {
            sendAction(TimerForegroundService.ACTION_DISMISS_ALARM)
        }

        override fun silenceAlarm() {
            sendAction(TimerForegroundService.ACTION_SILENCE_ALARM)
        }

        override fun pauseTimer() {
            sendAction(TimerForegroundService.ACTION_PAUSE)
        }

        override fun resumeTimer() {
            sendAction(TimerForegroundService.ACTION_RESUME)
        }

        override fun resetTimer() {
            sendAction(TimerForegroundService.ACTION_RESET)
        }

        override fun updateLoop(enabled: Boolean) {
            val intent =
                Intent(context, TimerForegroundService::class.java).apply {
                    action = TimerForegroundService.ACTION_UPDATE_LOOP
                    putExtra(TimerForegroundService.EXTRA_REPEAT_ENABLED, enabled)
                }
            context.startService(intent)
        }

        private fun sendAction(action: String) {
            val intent =
                Intent(context, TimerForegroundService::class.java).apply {
                    this.action = action
                    putExtra(TimerForegroundService.EXTRA_APP_IN_FOREGROUND, true)
                }
            context.startService(intent)
        }
    }
