package com.iganapolsky.randomtimer.service

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import org.junit.Test

class AlarmCompletionPolicyTest {
    @Test
    fun `manual alarm dismiss records completion only while alarm is active`() {
        assertThat(AlarmCompletionPolicy.shouldRecordManualDismissCompletion(TimerStatus.ALARM)).isTrue()
        assertThat(AlarmCompletionPolicy.shouldRecordManualDismissCompletion(TimerStatus.COMPLETE)).isFalse()
        assertThat(AlarmCompletionPolicy.shouldRecordManualDismissCompletion(TimerStatus.RUNNING)).isFalse()
        assertThat(AlarmCompletionPolicy.shouldRecordManualDismissCompletion(null)).isFalse()
    }
}
