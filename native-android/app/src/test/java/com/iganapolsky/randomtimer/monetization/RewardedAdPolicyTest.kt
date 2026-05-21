package com.iganapolsky.randomtimer.monetization

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class RewardedAdPolicyTest {
    @Test
    fun `does not offer when flag disabled`() {
        assertThat(RewardedAdPolicy.canOfferRewardedAd(rewardedAdsEnabled = false, isPro = false)).isFalse()
    }

    @Test
    fun `does not offer for pro users when flag enabled`() {
        assertThat(RewardedAdPolicy.canOfferRewardedAd(rewardedAdsEnabled = true, isPro = true)).isFalse()
    }

    @Test
    fun `offers for free users when flag enabled`() {
        assertThat(RewardedAdPolicy.canOfferRewardedAd(rewardedAdsEnabled = true, isPro = false)).isTrue()
    }

    @Test
    fun `unlock feature is pro sound trial`() {
        assertThat(RewardedAdPolicy.UNLOCK_FEATURE).isEqualTo("pro_sound_trial")
    }
}
