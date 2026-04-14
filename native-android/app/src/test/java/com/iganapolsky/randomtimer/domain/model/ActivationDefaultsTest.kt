package com.iganapolsky.randomtimer.domain.model

import com.google.common.truth.Truth.assertThat
import org.junit.Test
import kotlin.time.Duration.Companion.seconds

class ActivationDefaultsTest {
    @Test
    fun `default min is 5 seconds to prevent instant fire`() {
        assertThat(TimerConfig.DEFAULT.minSeconds).isEqualTo(5)
    }

    @Test
    fun `default max is 30 seconds for activation-first quick start`() {
        assertThat(TimerConfig.DEFAULT.maxSeconds).isEqualTo(30)
    }

    @Test
    fun `default config produces valid duration range`() {
        val config = TimerConfig.DEFAULT
        assertThat(config.maxSeconds).isGreaterThan(config.minSeconds)
        assertThat(config.maxSeconds - config.minSeconds).isAtLeast(5)
    }

    @Test
    fun `default min duration is 5 seconds`() {
        assertThat(TimerConfig.DEFAULT.minDuration).isEqualTo(5.seconds)
    }

    @Test
    fun `default max duration is 30 seconds`() {
        assertThat(TimerConfig.DEFAULT.maxDuration).isEqualTo(30.seconds)
    }

    @Test
    fun `activation preset min is at least 5 seconds`() {
        assertThat(TimerConfig.ACTIVATION_FIRST_RUN_MIN_SECONDS).isAtLeast(5)
    }

    @Test
    fun `MAX_SECONDS_FREE unchanged at 300`() {
        assertThat(TimerConfig.MAX_SECONDS_FREE).isEqualTo(300)
    }

    @Test
    fun `MAX_SECONDS_PRO unchanged at 3600`() {
        assertThat(TimerConfig.MAX_SECONDS_PRO).isEqualTo(3600)
    }
}
