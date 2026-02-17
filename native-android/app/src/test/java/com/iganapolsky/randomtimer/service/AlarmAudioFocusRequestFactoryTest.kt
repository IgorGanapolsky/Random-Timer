package com.iganapolsky.randomtimer.service

import android.media.AudioAttributes
import android.media.AudioManager
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class AlarmAudioFocusRequestFactoryTest {

    @Test
    fun `alarm audio focus requests transient may duck and will not pause when ducked`() {
        val spec = AlarmAudioFocusRequestFactory.spec()

        assertThat(spec.focusGain).isEqualTo(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
        assertThat(spec.willPauseWhenDucked).isFalse()
        assertThat(spec.usage).isEqualTo(AudioAttributes.USAGE_ALARM)
    }
}
