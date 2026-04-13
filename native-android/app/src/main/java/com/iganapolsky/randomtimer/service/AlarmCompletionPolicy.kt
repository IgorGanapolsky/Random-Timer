package com.iganapolsky.randomtimer.service

import com.iganapolsky.randomtimer.domain.model.TimerStatus

internal object AlarmCompletionPolicy {
    fun shouldRecordManualDismissCompletion(status: TimerStatus?): Boolean = status == TimerStatus.ALARM
}
