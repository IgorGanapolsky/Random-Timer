package com.iganapolsky.randomtimer.service

import com.iganapolsky.randomtimer.domain.model.TimerStatus

internal object AlarmPlaybackPolicy {
    fun shouldSilenceOnScreenOff(status: TimerStatus?): Boolean = status == TimerStatus.ALARM

    fun shouldRequestAudioFocus(status: TimerStatus?): Boolean = status == TimerStatus.ALARM
}
