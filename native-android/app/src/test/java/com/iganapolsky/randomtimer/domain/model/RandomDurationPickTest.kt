package com.iganapolsky.randomtimer.domain.model

import com.google.common.truth.Truth.assertThat
import org.junit.Test
import kotlin.random.Random

class RandomDurationPickTest {
    private class AlwaysPickLowerBound : Random() {
        override fun nextBits(bitCount: Int) = 0

        override fun nextLong(
            from: Long,
            until: Long,
        ) = from
    }

    @Test
    fun `floors at 1 second when max allows full second`() {
        val picked =
            pickRandomDurationMillisInclusive(0, 30_000, AlwaysPickLowerBound())
        assertThat(picked).isEqualTo(1000L)
    }

    @Test
    fun `does not raise min when already at least 1 second`() {
        val picked =
            pickRandomDurationMillisInclusive(5000, 10_000, AlwaysPickLowerBound())
        assertThat(picked).isEqualTo(5000L)
    }
}
