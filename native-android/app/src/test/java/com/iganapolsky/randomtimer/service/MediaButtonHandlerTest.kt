package com.iganapolsky.randomtimer.service

import android.view.KeyEvent
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class MediaButtonHandlerTest {

    @Test
    fun `ACTION_DOWN on play-pause silences alarm`() {
        val silence = MediaButtonHandler.shouldSilenceAlarm(
            keyCode = KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,
            action = KeyEvent.ACTION_DOWN
        )
        assertThat(silence).isTrue()
    }

    @Test
    fun `ACTION_UP is ignored`() {
        val silence = MediaButtonHandler.shouldSilenceAlarm(
            keyCode = KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,
            action = KeyEvent.ACTION_UP
        )
        assertThat(silence).isFalse()
    }

    @Test
    fun `ACTION_DOWN on volume up silences alarm`() {
        val silence =
            MediaButtonHandler.shouldSilenceAlarm(
                keyCode = KeyEvent.KEYCODE_VOLUME_UP,
                action = KeyEvent.ACTION_DOWN,
            )
        assertThat(silence).isTrue()
    }

    @Test
    fun `ACTION_DOWN on volume down silences alarm`() {
        val silence =
            MediaButtonHandler.shouldSilenceAlarm(
                keyCode = KeyEvent.KEYCODE_VOLUME_DOWN,
                action = KeyEvent.ACTION_DOWN,
            )
        assertThat(silence).isTrue()
    }

    @Test
    fun `unrelated key is ignored`() {
        val silence =
            MediaButtonHandler.shouldSilenceAlarm(
                keyCode = KeyEvent.KEYCODE_HOME,
                action = KeyEvent.ACTION_DOWN,
            )
        assertThat(silence).isFalse()
    }

    @Test
    fun `headset hook silences alarm`() {
        val silence = MediaButtonHandler.shouldSilenceAlarm(
            keyCode = KeyEvent.KEYCODE_HEADSETHOOK,
            action = KeyEvent.ACTION_DOWN
        )
        assertThat(silence).isTrue()
    }

    @Test
    fun `volume keys are identified`() {
        assertThat(MediaButtonHandler.isVolumeKey(KeyEvent.KEYCODE_VOLUME_UP)).isTrue()
        assertThat(MediaButtonHandler.isVolumeKey(KeyEvent.KEYCODE_VOLUME_DOWN)).isTrue()
        assertThat(MediaButtonHandler.isVolumeKey(KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE)).isFalse()
    }
}
