package com.iganapolsky.randomtimer.monetization

import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class RewardedAdAnalyticsTest {
    @Test
    fun `event names match hybrid monetization contract`() {
        assertThat(AnalyticsEvents.REWARDED_AD_REQUESTED).isEqualTo("rewarded_ad_requested")
        assertThat(AnalyticsEvents.REWARDED_AD_COMPLETED).isEqualTo("rewarded_ad_completed")
        assertThat(AnalyticsEvents.REWARDED_AD_UNLOCK).isEqualTo("rewarded_ad_unlock")
    }

    @Test
    fun `requested properties include unlock feature and phase`() {
        val props = RewardedAdAnalytics.requestedProperties("sound_arsenal_gate")
        assertThat(props["unlock_feature"]).isEqualTo(RewardedAdPolicy.UNLOCK_FEATURE)
        assertThat(props["monetization_phase"]).isEqualTo("p1_rewarded_ads")
        assertThat(props["entry_point"]).isEqualTo("sound_arsenal_gate")
    }
}
