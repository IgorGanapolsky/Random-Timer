package com.iganapolsky.randomtimer.billing

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.AcknowledgePurchaseParams
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetailsResult
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import com.android.billingclient.api.acknowledgePurchase
import com.android.billingclient.api.queryProductDetails
import com.android.billingclient.api.queryPurchasesAsync
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ProManager
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
    ) : PurchasesUpdatedListener {
        companion object {
            const val PRODUCT_ID = "pro_upgrade"
        }

        private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

        private val _isPro = MutableStateFlow(false)
        val isPro: StateFlow<Boolean> = _isPro

        private var billingClient: BillingClient =
            BillingClient
                .newBuilder(context)
                .setListener(this)
                .enablePendingPurchases(
                    PendingPurchasesParams
                        .newBuilder()
                        .enableOneTimeProducts()
                        .build(),
                ).build()

        private var cachedProductDetails: com.android.billingclient.api.ProductDetails? = null

        init {
            connectAndRestore()
        }

        private fun connectAndRestore() {
            billingClient.startConnection(
                object : BillingClientStateListener {
                    override fun onBillingSetupFinished(result: BillingResult) {
                        if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                            scope.launch { restorePurchases() }
                        }
                    }

                    override fun onBillingServiceDisconnected() {
                        // Retry on next purchase attempt
                    }
                },
            )
        }

        private suspend fun restorePurchases() {
            val params =
                QueryPurchasesParams
                    .newBuilder()
                    .setProductType(BillingClient.ProductType.INAPP)
                    .build()
            val result = billingClient.queryPurchasesAsync(params)
            val hasPro =
                result.purchasesList.any { purchase ->
                    purchase.products.contains(PRODUCT_ID) &&
                        purchase.purchaseState == Purchase.PurchaseState.PURCHASED
                }
            _isPro.value = hasPro
        }

        suspend fun launchPurchase(activity: Activity): Boolean {
            if (!billingClient.isReady) {
                connectAndRestore()
                return false
            }

            val productDetails = cachedProductDetails ?: fetchProductDetails() ?: return false
            cachedProductDetails = productDetails

            val productDetailsParamsList =
                listOf(
                    BillingFlowParams.ProductDetailsParams
                        .newBuilder()
                        .setProductDetails(productDetails)
                        .build(),
                )

            val flowParams =
                BillingFlowParams
                    .newBuilder()
                    .setProductDetailsParamsList(productDetailsParamsList)
                    .build()

            val result = billingClient.launchBillingFlow(activity, flowParams)
            return result.responseCode == BillingClient.BillingResponseCode.OK
        }

        private suspend fun fetchProductDetails(): com.android.billingclient.api.ProductDetails? {
            val productList =
                listOf(
                    QueryProductDetailsParams.Product
                        .newBuilder()
                        .setProductId(PRODUCT_ID)
                        .setProductType(BillingClient.ProductType.INAPP)
                        .build(),
                )

            val params =
                QueryProductDetailsParams
                    .newBuilder()
                    .setProductList(productList)
                    .build()

            val result: ProductDetailsResult = billingClient.queryProductDetails(params)
            return result.productDetailsList?.firstOrNull()
        }

        suspend fun getFormattedPrice(): String {
            val details = cachedProductDetails ?: fetchProductDetails()
            cachedProductDetails = details
            return details
                ?.oneTimePurchaseOfferDetails
                ?.formattedPrice
                ?: "$4.99"
        }

        override fun onPurchasesUpdated(
            result: BillingResult,
            purchases: MutableList<Purchase>?,
        ) {
            if (result.responseCode == BillingClient.BillingResponseCode.OK && purchases != null) {
                for (purchase in purchases) {
                    if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
                        _isPro.value = true
                        scope.launch { acknowledgePurchaseIfNeeded(purchase) }
                    }
                }
            }
        }

        private suspend fun acknowledgePurchaseIfNeeded(purchase: Purchase) {
            if (!purchase.isAcknowledged) {
                val params =
                    AcknowledgePurchaseParams
                        .newBuilder()
                        .setPurchaseToken(purchase.purchaseToken)
                        .build()
                billingClient.acknowledgePurchase(params)
            }
        }

        // Feature gates

        fun maxSecondsLimit(isPro: Boolean = _isPro.value): Int = if (isPro) TimerConfig.MAX_SECONDS_PRO else TimerConfig.MAX_SECONDS_FREE

        fun availableSounds(isPro: Boolean = _isPro.value): List<SoundType> = if (isPro) SoundType.entries.toList() else SoundType.FREE
    }
