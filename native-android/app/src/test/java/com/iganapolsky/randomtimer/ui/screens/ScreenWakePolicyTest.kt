package com.iganapolsky.randomtimer.ui.screens

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import org.junit.Test
import kotlin.time.Duration.Companion.seconds

class ScreenWakePolicyTest {
    @Test
    fun `keeps screen awake while timer state exists`() {
        TimerStatus.entries
            .filter { it != TimerStatus.IDLE && it != TimerStatus.COMPLETE }
            .forEach { status ->
                val state =
                    TimerState(
                        config = TimerConfig.DEFAULT,
                        targetDuration = 30.seconds,
                        remainingDuration = 15.seconds,
                        status = status,
                    )

                assertThat(shouldKeepScreenAwake(state)).isTrue()
            }
    }

    @Test
    fun `allows screen sleep when timer is complete`() {
        val completeState =
            TimerState(
                config = TimerConfig.DEFAULT,
                targetDuration = 30.seconds,
                remainingDuration = 0.seconds,
                status = TimerStatus.COMPLETE,
            )

        assertThat(shouldKeepScreenAwake(completeState)).isFalse()
    }

    @Test
    fun `allows screen sleep when timer state is absent`() {
        assertThat(shouldKeepScreenAwake(null)).isFalse()
    }
}
