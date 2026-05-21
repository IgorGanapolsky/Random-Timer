package com.iganapolsky.randomtimer.monetization

import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsService

/**
 * Rewarded ad port. [StubRewardedAdController] is the default until AdMob SDK + publisher account ship.
 */
fun interface RewardedAdPort {
    fun showRewardedAd(
        entryPoint: String,
        onFinished: (success: Boolean) -> Unit,
    )
}

class RewardedAdCoordinator(
    private val analyticsService: AnalyticsService,
    private val unlockStore: RewardedAdUnlockStore,
    private val port: RewardedAdPort = StubRewardedAdPort(),
) {
    fun requestUnlock(
        entryPoint: String,
        rewardedAdsEnabled: Boolean,
        isPro: Boolean,
        onUnlocked: () -> Unit,
    ) {
        if (!RewardedAdPolicy.canOfferRewardedAd(rewardedAdsEnabled, isPro)) return

        analyticsService.track(
            AnalyticsEvents.REWARDED_AD_REQUESTED,
            RewardedAdAnalytics.requestedProperties(entryPoint),
        )
        port.showRewardedAd(entryPoint) { success ->
            analyticsService.track(
                AnalyticsEvents.REWARDED_AD_COMPLETED,
                RewardedAdAnalytics.completedProperties(entryPoint, success),
            )
            if (success) {
                unlockStore.grantUnlock()
                analyticsService.track(
                    AnalyticsEvents.REWARDED_AD_UNLOCK,
                    RewardedAdAnalytics.unlockProperties(entryPoint),
                )
                onUnlocked()
            }
        }
    }
}

/** No-op until AdMob SDK is integrated (flag stays off in production). */
class StubRewardedAdPort : RewardedAdPort {
    override fun showRewardedAd(
        entryPoint: String,
        onFinished: (success: Boolean) -> Unit,
    ) {
        onFinished(false)
    }
}
