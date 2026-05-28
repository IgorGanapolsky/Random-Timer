package com.iganapolsky.randomtimer.monetization

import android.app.Activity
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.MobileAds
import com.google.android.gms.ads.rewarded.RewardedAd
import com.google.android.gms.ads.rewarded.RewardedAdLoadCallback
import com.iganapolsky.randomtimer.BuildConfig

/**
 * Loads and shows AdMob rewarded ads. Requires [ForegroundActivityHolder] and PostHog
 * `rewarded_ads_enabled` at the call site ([RewardedAdCoordinator]).
 */
class AdMobRewardedAdPort : RewardedAdPort {
    @Volatile
    private var initialized = false

    override fun showRewardedAd(
        entryPoint: String,
        onFinished: (success: Boolean) -> Unit,
    ) {
        val activity = ForegroundActivityHolder.getActivity()
        if (activity == null) {
            onFinished(false)
            return
        }
        ensureInitialized(activity)
        val unitId = RewardedAdConfig.resolvedRewardedUnitId(useTestAds = BuildConfig.DEBUG)
        RewardedAd.load(
            activity,
            unitId,
            AdRequest.Builder().build(),
            object : RewardedAdLoadCallback() {
                override fun onAdFailedToLoad(error: LoadAdError) {
                    onFinished(false)
                }

                override fun onAdLoaded(ad: RewardedAd) {
                    var rewarded = false
                    ad.fullScreenContentCallback =
                        object : com.google.android.gms.ads.FullScreenContentCallback() {
                            override fun onAdDismissedFullScreenContent() {
                                if (!rewarded) {
                                    onFinished(false)
                                }
                            }

                            override fun onAdFailedToShowFullScreenContent(
                                adError: com.google.android.gms.ads.AdError,
                            ) {
                                onFinished(false)
                            }
                        }
                    ad.show(activity) {
                        rewarded = true
                        onFinished(true)
                    }
                }
            },
        )
    }

    private fun ensureInitialized(activity: Activity) {
        if (initialized) return
        synchronized(this) {
            if (initialized) return
            MobileAds.initialize(activity.applicationContext) {}
            initialized = true
        }
    }
}
