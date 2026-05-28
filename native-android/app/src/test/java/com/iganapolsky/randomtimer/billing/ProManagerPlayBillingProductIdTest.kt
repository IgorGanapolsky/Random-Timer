package com.iganapolsky.randomtimer.billing

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class ProManagerPlayBillingProductIdTest {
    @Test
    fun `playBillingProductId uses Play catalog product ids`() {
        assertThat(playBillingProductId(ProManager.MONTHLY_PRODUCT_ID))
            .isEqualTo(ProManager.MONTHLY_PRODUCT_ID)
    }

    @Test
    fun `playBillingProductId leaves elite and base ids unchanged`() {
        assertThat(playBillingProductId(ProManager.ELITE_PRODUCT_ID))
            .isEqualTo(ProManager.ELITE_PRODUCT_ID)
        assertThat(playBillingProductId(ProManager.BASE_PRODUCT_ID))
            .isEqualTo(ProManager.BASE_PRODUCT_ID)
    }

    @Test
    fun `monthlyOfferAvailableFromEliteDetails true when P1M offer exists`() {
        val eliteOffers =
            listOf(
                SubscriptionOffer(
                    offerToken = "annual",
                    pricingPhases =
                        listOf(
                            SubscriptionPricingPhase(
                                formattedPrice = "$29.99",
                                billingPeriod = "P1Y",
                            ),
                        ),
                ),
                SubscriptionOffer(
                    offerToken = "monthly",
                    pricingPhases =
                        listOf(
                            SubscriptionPricingPhase(
                                formattedPrice = "$3.99",
                                billingPeriod = "P1M",
                            ),
                        ),
                ),
            )

        assertThat(monthlyOfferAvailableFromEliteOffers(eliteOffers)).isTrue()
    }

    @Test
    fun `monthlyOfferAvailableFromEliteDetails false without P1M`() {
        val annualOnly =
            listOf(
                SubscriptionOffer(
                    offerToken = "annual",
                    pricingPhases =
                        listOf(
                            SubscriptionPricingPhase(
                                formattedPrice = "$29.99",
                                billingPeriod = "P1Y",
                            ),
                        ),
                ),
            )

        assertThat(monthlyOfferAvailableFromEliteOffers(annualOnly)).isFalse()
    }
}
