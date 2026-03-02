package com.iganapolsky.randomtimer.service

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import org.junit.Test

class AlarmPlaybackPolicyTest {
    @Test
    fun `screen off should silence only while alarm is active`() {
        assertThat(AlarmPlaybackPolicy.shouldSilenceOnScreenOff(TimerStatus.ALARM)).isTrue()
        assertThat(AlarmPlaybackPolicy.shouldSilenceOnScreenOff(TimerStatus.RUNNING)).isFalse()
        assertThat(AlarmPlaybackPolicy.shouldSilenceOnScreenOff(TimerStatus.COMPLETE)).isFalse()
        assertThat(AlarmPlaybackPolicy.shouldSilenceOnScreenOff(null)).isFalse()
    }

    @Test
    fun `audio focus requested only for alarm state`() {
        assertThat(AlarmPlaybackPolicy.shouldRequestAudioFocus(TimerStatus.ALARM)).isTrue()
        assertThat(AlarmPlaybackPolicy.shouldRequestAudioFocus(TimerStatus.PAUSED)).isFalse()
        assertThat(AlarmPlaybackPolicy.shouldRequestAudioFocus(TimerStatus.IDLE)).isFalse()
    }
}
