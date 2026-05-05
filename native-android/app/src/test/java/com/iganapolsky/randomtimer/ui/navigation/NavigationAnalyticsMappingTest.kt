package com.iganapolsky.randomtimer.ui.navigation

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class NavigationAnalyticsMappingTest {
    @Test
    fun rangeUpgradeMapsToRangeGateEntryPoint() {
        assertThat(paywallEntryPointForFeature("extended_range")).isEqualTo("range_gate")
    }

    @Test
    fun setupUpgradeMapsToCanonicalSetupEntryPoint() {
        assertThat(paywallEntryPointForFeature("setup_upgrade_cta")).isEqualTo("setup_upgrade_cta")
    }

    @Test
    fun upgradeSurfacesMapToDistinctIntentEntryPoints() {
        assertThat(paywallEntryPointForFeature("voice_callouts")).isEqualTo("voice_gate")
        assertThat(paywallEntryPointForFeature("pro_sounds")).isEqualTo("sound_arsenal_gate")
        assertThat(paywallEntryPointForFeature("repeat_loop")).isEqualTo("repeat_gate")
    }

    @Test
    fun unknownUpgradeFallsBackToUnknownEntryPoint() {
        assertThat(paywallEntryPointForFeature("mystery_feature")).isEqualTo("unknown")
    }
}
