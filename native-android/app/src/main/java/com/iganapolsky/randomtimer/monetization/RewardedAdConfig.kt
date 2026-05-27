package com.iganapolsky.randomtimer.monetization

import com.iganapolsky.randomtimer.analytics.PostHogExperimentKeys

/**
 * Rewarded ads (IAA) configuration. SDK not wired until CEO approves AdMob publisher account.
 * Google test unit ID is documented for debug wiring; production IDs come from env/Play Console.
 */
object RewardedAdConfig {
    val featureFlagKey: String = PostHogExperimentKeys.REWARDED_ADS_ENABLED

    /** Official Google test rewarded unit (Android). */
    const val TEST_REWARDED_UNIT_ID_ANDROID = "ca-app-pub-3940256099942544/5224354917"

    /** Official Google test rewarded unit (iOS). */
    const val TEST_REWARDED_UNIT_ID_IOS = "ca-app-pub-3940256099942544/1712485313"

    const val PUBLISHER_ID = "pub-5173650670360699"

    const val ADMOB_BLOCKER =
        "Rewarded ads ship behind PostHog flag (default off) until ADMOB_* unit env IDs are set and app-ads.txt verifies."
}
