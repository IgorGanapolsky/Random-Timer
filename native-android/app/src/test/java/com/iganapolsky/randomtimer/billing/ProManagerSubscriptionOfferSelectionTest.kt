package com.iganapolsky.randomtimer.billing

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class ProManagerSubscriptionOfferSelectionTest {
    @Test
    fun `selectPreferredSubscriptionOffer prefers yearly billing phase`() {
        val monthly =
            SubscriptionOffer(
                offerToken = "monthly-token",
                pricingPhases =
                    listOf(
                        SubscriptionPricingPhase(
                            formattedPrice = "$4.99",
                            billingPeriod = "P1M",
                        ),
                    ),
            )
        val yearly =
            SubscriptionOffer(
                offerToken = "yearly-token",
                pricingPhases =
                    listOf(
                        SubscriptionPricingPhase(
                            formattedPrice = "$29.99",
                            billingPeriod = "P1Y",
                        ),
                    ),
            )

        val selected = selectPreferredSubscriptionOffer(listOf(monthly, yearly))

        assertThat(selected?.offerToken).isEqualTo("yearly-token")
        assertThat(selected?.displayPrice).isEqualTo("$29.99")
    }

    @Test
    fun `selectPreferredSubscriptionOffer falls back to first offer when yearly is unavailable`() {
        val monthly =
            SubscriptionOffer(
                offerToken = "monthly-token",
                pricingPhases =
                    listOf(
                        SubscriptionPricingPhase(
                            formattedPrice = "$4.99",
                            billingPeriod = "P1M",
                        ),
                    ),
            )
        val monthlyWithIntro =
            SubscriptionOffer(
                offerToken = "monthly-intro-token",
                pricingPhases =
                    listOf(
                        SubscriptionPricingPhase(
                            formattedPrice = "$0.99",
                            billingPeriod = "P1W",
                        ),
                        SubscriptionPricingPhase(
                            formattedPrice = "$4.99",
                            billingPeriod = "P1M",
                        ),
                    ),
            )

        val selected = selectPreferredSubscriptionOffer(listOf(monthly, monthlyWithIntro))

        assertThat(selected?.offerToken).isEqualTo("monthly-token")
        assertThat(selected?.displayPrice).isEqualTo("$4.99")
    }
}
