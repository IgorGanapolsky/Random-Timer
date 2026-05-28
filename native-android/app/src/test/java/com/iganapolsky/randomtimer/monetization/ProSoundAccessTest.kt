package com.iganapolsky.randomtimer.monetization

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.SoundType
import org.junit.Test

class ProSoundAccessTest {
    @Test
    fun `pro users can equip pro sounds`() {
        assertThat(ProSoundAccess.canEquipProSound(isPro = true, hasTrialUnlock = false)).isTrue()
    }

    @Test
    fun `trial unlock allows equip without subscription`() {
        assertThat(ProSoundAccess.canEquipProSound(isPro = false, hasTrialUnlock = true)).isTrue()
    }

    @Test
    fun `free users without trial cannot equip`() {
        assertThat(ProSoundAccess.canEquipProSound(isPro = false, hasTrialUnlock = false)).isFalse()
    }

    @Test
    fun `consumes trial when equipping first pro sound`() {
        assertThat(
            ProSoundAccess.shouldConsumeTrialOnEquip(
                isPro = false,
                hasTrialUnlock = true,
                previousSound = SoundType.INTENSE,
                newSound = SoundType.KLAXON,
            ),
        ).isTrue()
    }

    @Test
    fun `does not consume when switching between pro sounds`() {
        assertThat(
            ProSoundAccess.shouldConsumeTrialOnEquip(
                isPro = false,
                hasTrialUnlock = true,
                previousSound = SoundType.KLAXON,
                newSound = SoundType.WHISTLE,
            ),
        ).isFalse()
    }
}
