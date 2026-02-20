package com.iganapolsky.randomtimer.receiver

import android.content.Context
import android.content.Intent
import com.google.common.truth.Truth.assertThat
import io.mockk.mockk
import io.mockk.every
import org.junit.Test

class ScreenOffReceiverTest {

    @Test
    fun `ACTION_SCREEN_OFF triggers silence callback`() {
        var silenced = false
        val receiver = ScreenOffReceiver { silenced = true }
        val context = mockk<Context>()
        val intent = mockk<Intent> {
            every { action } returns Intent.ACTION_SCREEN_OFF
        }

        receiver.onReceive(context, intent)

        assertThat(silenced).isTrue()
    }

    @Test
    fun `other actions do not trigger callback`() {
        var silenced = false
        val receiver = ScreenOffReceiver { silenced = true }
        val context = mockk<Context>()
        val intent = mockk<Intent> {
            every { action } returns Intent.ACTION_SCREEN_ON
        }

        receiver.onReceive(context, intent)

        assertThat(silenced).isFalse()
    }

    @Test
    fun `null action does not trigger callback`() {
        var silenced = false
        val receiver = ScreenOffReceiver { silenced = true }
        val context = mockk<Context>()
        val intent = mockk<Intent> {
            every { action } returns null
        }

        receiver.onReceive(context, intent)

        assertThat(silenced).isFalse()
    }
}
