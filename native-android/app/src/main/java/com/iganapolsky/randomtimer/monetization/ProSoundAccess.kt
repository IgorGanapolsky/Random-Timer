package com.iganapolsky.randomtimer.monetization

import com.iganapolsky.randomtimer.domain.model.SoundType

/** Free-tier Pro sound access via subscription or rewarded-ad trial unlock. */
object ProSoundAccess {
    fun canEquipProSound(
        isPro: Boolean,
        hasTrialUnlock: Boolean,
    ): Boolean = isPro || hasTrialUnlock

    fun shouldConsumeTrialOnEquip(
        isPro: Boolean,
        hasTrialUnlock: Boolean,
        previousSound: SoundType,
        newSound: SoundType,
    ): Boolean =
        !isPro &&
            hasTrialUnlock &&
            newSound in SoundType.PRO &&
            previousSound !in SoundType.PRO
}
