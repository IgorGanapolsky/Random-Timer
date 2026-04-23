package com.iganapolsky.randomtimer.ui.navigation

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class NavigationAnalyticsMappingTest {
    @Test
    fun rangeUpgradeMapsToRangeGateEntryPoint() {
        assertThat(paywallEntryPointForFeature("extended_range")).isEqualTo("range_gate")
    }

    @Test
    fun soundAndLoopUpgradesMapToSoundGateEntryPoint() {
        assertThat(paywallEntryPointForFeature("voice_callouts")).isEqualTo("sound_gate")
        assertThat(paywallEntryPointForFeature("pro_sounds")).isEqualTo("sound_gate")
        assertThat(paywallEntryPointForFeature("repeat_loop")).isEqualTo("sound_gate")
    }

    @Test
    fun unknownUpgradeFallsBackToSetupCtaEntryPoint() {
        assertThat(paywallEntryPointForFeature("mystery_feature")).isEqualTo("setup_upgrade_cta")
    }
}
