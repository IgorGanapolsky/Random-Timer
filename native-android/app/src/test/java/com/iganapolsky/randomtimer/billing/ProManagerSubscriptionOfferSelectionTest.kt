package com.iganapolsky.randomtimer.billing

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class ProManagerSubscriptionOfferSelectionTest {
    @Test
    fun `selectPreferredSubscriptionOffer prefers free-trial offer over annual`() {
        val annual =
            SubscriptionOffer(
                offerToken = "yearly-token",
                pricingPhases =
                    listOf(
                        SubscriptionPricingPhase(
                            formattedPrice = "$29.99",
                            billingPeriod = "P1Y",
                            isFree = false,
                        ),
                    ),
            )
        val trialThenAnnual =
            SubscriptionOffer(
                offerToken = "trial-annual-token",
                pricingPhases =
                    listOf(
                        SubscriptionPricingPhase(
                            formattedPrice = "$0.00",
                            billingPeriod = "P7D",
                            isFree = true,
                        ),
                        SubscriptionPricingPhase(
                            formattedPrice = "$29.99",
                            billingPeriod = "P1Y",
                            isFree = false,
                        ),
                    ),
            )

        val selected = selectPreferredSubscriptionOffer(listOf(annual, trialThenAnnual))

        assertThat(selected?.offerToken).isEqualTo("trial-annual-token")
        assertThat(selected?.hasFreeTrial).isTrue()
    }

    @Test
    fun `selectPreferredSubscriptionOffer prefers yearly billing phase when no free trial`() {
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
    fun `selectPreferredSubscriptionOffer falls back to first offer when no trial and no annual`() {
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

        val selected = selectPreferredSubscriptionOffer(listOf(monthly))

        assertThat(selected?.offerToken).isEqualTo("monthly-token")
    }

    @Test
    fun `SubscriptionOffer hasFreeTrial is true when any phase is free`() {
        val offerWithTrial =
            SubscriptionOffer(
                offerToken = "trial-token",
                pricingPhases =
                    listOf(
                        SubscriptionPricingPhase(
                            formattedPrice = "$0.00",
                            billingPeriod = "P7D",
                            isFree = true,
                        ),
                        SubscriptionPricingPhase(
                            formattedPrice = "$29.99",
                            billingPeriod = "P1Y",
                            isFree = false,
                        ),
                    ),
            )

        assertThat(offerWithTrial.hasFreeTrial).isTrue()
    }

    @Test
    fun `SubscriptionOffer hasFreeTrial is false when no phase is free`() {
        val offerWithoutTrial =
            SubscriptionOffer(
                offerToken = "paid-token",
                pricingPhases =
                    listOf(
                        SubscriptionPricingPhase(
                            formattedPrice = "$29.99",
                            billingPeriod = "P1Y",
                            isFree = false,
                        ),
                    ),
            )

        assertThat(offerWithoutTrial.hasFreeTrial).isFalse()
    }
}
