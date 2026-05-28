package com.iganapolsky.randomtimer.monetization

import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import io.mockk.mockk
import io.mockk.verify
import org.junit.Before
import org.junit.Test

class RewardedAdCoordinatorTest {
    private lateinit var analyticsService: AnalyticsService
    private lateinit var unlockStore: RewardedAdUnlockStore
    private lateinit var port: RecordingRewardedAdPort
    private lateinit var coordinator: RewardedAdCoordinator

    @Before
    fun setup() {
        analyticsService = mockk(relaxed = true)
        unlockStore = mockk(relaxed = true)
        port = RecordingRewardedAdPort()
        coordinator =
            RewardedAdCoordinator(
                analyticsService = analyticsService,
                unlockStore = unlockStore,
                port = port,
            )
    }

    @Test
    fun `grants unlock and tracks when ad completes`() {
        var unlocked = false
        port.nextSuccess = true

        coordinator.requestUnlock(
            entryPoint = RewardedAdPolicy.ENTRY_SOUND_ARSENAL,
            rewardedAdsEnabled = true,
            isPro = false,
            onUnlocked = { unlocked = true },
        )

        assertThat(unlocked).isTrue()
        verify { unlockStore.grantUnlock() }
        verify {
            analyticsService.track(
                AnalyticsEvents.REWARDED_AD_UNLOCK,
                any(),
            )
        }
    }

    @Test
    fun `does not grant when flag disabled`() {
        coordinator.requestUnlock(
            entryPoint = RewardedAdPolicy.ENTRY_SOUND_ARSENAL,
            rewardedAdsEnabled = false,
            isPro = false,
            onUnlocked = {},
        )

        assertThat(port.showCount).isEqualTo(0)
        verify(exactly = 0) { unlockStore.grantUnlock() }
    }

    private class RecordingRewardedAdPort : RewardedAdPort {
        var nextSuccess = false
        var showCount = 0

        override fun showRewardedAd(
            entryPoint: String,
            onFinished: (success: Boolean) -> Unit,
        ) {
            showCount++
            onFinished(nextSuccess)
        }
    }
}
