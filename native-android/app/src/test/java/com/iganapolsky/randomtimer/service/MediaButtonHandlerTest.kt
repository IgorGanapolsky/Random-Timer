package com.iganapolsky.randomtimer.service

import android.view.KeyEvent
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class MediaButtonHandlerTest {

    @Test
    fun `ACTION_DOWN on play-pause dismisses alarm`() {
        val dismiss = MediaButtonHandler.shouldDismissAlarm(
            keyCode = KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,
            action = KeyEvent.ACTION_DOWN
        )
        assertThat(dismiss).isTrue()
    }

    @Test
    fun `ACTION_UP is ignored`() {
        val dismiss = MediaButtonHandler.shouldDismissAlarm(
            keyCode = KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,
            action = KeyEvent.ACTION_UP
        )
        assertThat(dismiss).isFalse()
    }

    @Test
    fun `non-media key is ignored`() {
        val dismiss = MediaButtonHandler.shouldDismissAlarm(
            keyCode = KeyEvent.KEYCODE_VOLUME_UP,
            action = KeyEvent.ACTION_DOWN
        )
        assertThat(dismiss).isFalse()
    }

    @Test
    fun `headset hook dismisses alarm`() {
        val dismiss = MediaButtonHandler.shouldDismissAlarm(
            keyCode = KeyEvent.KEYCODE_HEADSETHOOK,
            action = KeyEvent.ACTION_DOWN
        )
        assertThat(dismiss).isTrue()
    }
}

