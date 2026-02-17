package com.iganapolsky.randomtimer.service

import android.content.ServiceConnection
import com.iganapolsky.randomtimer.domain.model.TimerState

interface TimerServiceController {
    fun bindService(connection: ServiceConnection)
    fun unbindService(connection: ServiceConnection)
    fun startTimer(state: TimerState)
    fun stopTimer()
    fun dismissAlarm()
    fun silenceAlarm()
    fun pauseTimer()
    fun resumeTimer()
    fun resetTimer()
    fun updateLoop(enabled: Boolean)
}
