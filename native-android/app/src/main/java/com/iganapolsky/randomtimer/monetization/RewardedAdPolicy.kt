package com.iganapolsky.randomtimer.monetization

/** Free-tier rewarded video: unlock one Pro sound trial per completed ad (when flag + SDK live). */
object RewardedAdPolicy {
    const val UNLOCK_FEATURE = "pro_sound_trial"
    const val ENTRY_SOUND_ARSENAL = "sound_arsenal_gate"

    fun canOfferRewardedAd(
        rewardedAdsEnabled: Boolean,
        isPro: Boolean,
    ): Boolean = rewardedAdsEnabled && !isPro
}
