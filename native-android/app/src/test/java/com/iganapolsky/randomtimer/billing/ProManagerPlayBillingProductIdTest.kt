package com.iganapolsky.randomtimer.billing

import com.android.billingclient.api.BillingClient
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class ProManagerPlayBillingProductIdTest {
    @Test
    fun `billingProductTypeForLogicalProductId treats monthly subscription as SUBS`() {
        assertThat(billingProductTypeForLogicalProductId(ProManager.MONTHLY_PRODUCT_ID))
            .isEqualTo(BillingClient.ProductType.SUBS)
    }

    @Test
    fun `billingProductTypeForLogicalProductId treats annual elite as SUBS and base as INAPP`() {
        assertThat(billingProductTypeForLogicalProductId(ProManager.ELITE_PRODUCT_ID))
            .isEqualTo(BillingClient.ProductType.SUBS)
        assertThat(billingProductTypeForLogicalProductId(ProManager.BASE_PRODUCT_ID))
            .isEqualTo(BillingClient.ProductType.INAPP)
    }
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
