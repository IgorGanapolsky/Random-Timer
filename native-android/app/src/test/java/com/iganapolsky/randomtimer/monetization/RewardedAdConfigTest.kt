package com.iganapolsky.randomtimer.monetization

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class RewardedAdConfigTest {
    @Test
    fun `resolvedRewardedUnitId uses test id in test mode`() {
        assertThat(RewardedAdConfig.resolvedRewardedUnitId(useTestAds = true))
            .isEqualTo(RewardedAdConfig.TEST_REWARDED_UNIT_ID_ANDROID)
    }

    @Test
    fun `production constants match AdMob console`() {
        assertThat(RewardedAdConfig.PRODUCTION_APP_ID_ANDROID)
            .isEqualTo("ca-app-pub-5173650670360699~4427145410")
        assertThat(RewardedAdConfig.PRODUCTION_REWARDED_UNIT_ID_ANDROID)
            .isEqualTo("ca-app-pub-5173650670360699/8693693481")
    }
}
