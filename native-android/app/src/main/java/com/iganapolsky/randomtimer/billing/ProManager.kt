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
import com.iganapolsky.randomtimer.BuildConfig
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsProperties
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.domain.model.EntitlementLevel
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ProManager
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
        private val analyticsService: AnalyticsService,
        private val externalScope: CoroutineScope,
    ) : PurchasesUpdatedListener {
        companion object {
            const val BASE_PRODUCT_ID = "pro_base"
            const val ELITE_PRODUCT_ID = "elite_tactical"

            internal fun canUseDebugUnlock(isDebugBuild: Boolean = BuildConfig.DEBUG): Boolean = isDebugBuild
        }

        private val _entitlementLevel = MutableStateFlow(EntitlementLevel.NONE)
        val entitlementLevel: StateFlow<EntitlementLevel> = _entitlementLevel.asStateFlow()

        val isPro: StateFlow<Boolean> =
            _entitlementLevel
                .map { it.isPro }
                .stateIn(externalScope, SharingStarted.Eagerly, _entitlementLevel.value.isPro)

        val isElite: StateFlow<Boolean> =
            _entitlementLevel
                .map { it == EntitlementLevel.ELITE }
                .stateIn(externalScope, SharingStarted.Eagerly, _entitlementLevel.value == EntitlementLevel.ELITE)

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

        private val cachedProductDetails = mutableMapOf<String, com.android.billingclient.api.ProductDetails>()
        private var pendingPurchaseEntryPoint: String? = null

        init {
            connectAndRestore()
        }

        private fun connectAndRestore() {
            billingClient.startConnection(
                object : BillingClientStateListener {
                    override fun onBillingSetupFinished(result: BillingResult) {
                        if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                            externalScope.launch {
                                restorePurchases(
                                    source = MonetizationSources.AUTO_RESTORE,
                                    entryPoint = null,
                                    trackResult = false,
                                )
                                fetchAllProductDetails()
                            }
                        }
                    }

                    override fun onBillingServiceDisconnected() {
                        // Retry on next purchase attempt
                    }
                },
            )
        }

        private suspend fun restorePurchases(
            source: String,
            entryPoint: String?,
            trackResult: Boolean,
        ): Boolean {
            if (!billingClient.isReady) {
                connectAndRestore()
                if (trackResult) {
                    trackRestoreResult(
                        success = false,
                        source = source,
                        entryPoint = entryPoint,
                        responseCode = BillingClient.BillingResponseCode.SERVICE_DISCONNECTED,
                        debugMessage = "billing_not_ready",
                    )
                }
                return false
            }

            // Check In-App (BASE)
            val inAppParams =
                QueryPurchasesParams
                    .newBuilder()
                    .setProductType(BillingClient.ProductType.INAPP)
                    .build()
            val inAppResult = billingClient.queryPurchasesAsync(inAppParams)

            // Check Subs (ELITE)
            val subsParams =
                QueryPurchasesParams
                    .newBuilder()
                    .setProductType(BillingClient.ProductType.SUBS)
                    .build()
            val subsResult = billingClient.queryPurchasesAsync(subsParams)

            val hasElite =
                subsResult.purchasesList.any { purchase ->
                    purchase.products.contains(ELITE_PRODUCT_ID) &&
                        purchase.purchaseState == Purchase.PurchaseState.PURCHASED
                }

            val hasBase =
                inAppResult.purchasesList.any { purchase ->
                    purchase.products.contains(BASE_PRODUCT_ID) &&
                        purchase.purchaseState == Purchase.PurchaseState.PURCHASED
                }

            val level =
                when {
                    hasElite -> EntitlementLevel.ELITE
                    hasBase -> EntitlementLevel.BASE
                    else -> EntitlementLevel.NONE
                }

            _entitlementLevel.value = level

            if (trackResult) {
                trackRestoreResult(
                    success = level.isPro,
                    source = source,
                    entryPoint = entryPoint,
                    responseCode = if (hasElite) subsResult.billingResult.responseCode else inAppResult.billingResult.responseCode,
                    debugMessage = if (hasElite) subsResult.billingResult.debugMessage else inAppResult.billingResult.debugMessage,
                )
            }
            return level.isPro
        }

        suspend fun launchPurchase(
            activity: Activity,
            productID: String,
            entryPoint: String,
        ): Boolean {
            pendingPurchaseEntryPoint = entryPoint
            if (!billingClient.isReady) {
                connectAndRestore()
                trackPurchaseResult(
                    success = false,
                    source = MonetizationSources.PAYWALL,
                    entryPoint = entryPoint,
                    responseCode = BillingClient.BillingResponseCode.SERVICE_DISCONNECTED,
                    debugMessage = "billing_not_ready",
                )
                pendingPurchaseEntryPoint = null
                return false
            }

            val productDetails = cachedProductDetails[productID] ?: fetchProductDetails(productID)
            if (productDetails == null) {
                trackPurchaseResult(
                    success = false,
                    source = MonetizationSources.PAYWALL,
                    entryPoint = entryPoint,
                    responseCode = BillingClient.BillingResponseCode.ITEM_UNAVAILABLE,
                    debugMessage = "product_details_unavailable",
                )
                pendingPurchaseEntryPoint = null
                return false
            }
            cachedProductDetails[productID] = productDetails

            val productDetailsParamsList =
                listOf(
                    BillingFlowParams.ProductDetailsParams
                        .newBuilder()
                        .setProductDetails(productDetails)
                        .apply {
                            if (productID == ELITE_PRODUCT_ID) {
                                productDetails.subscriptionOfferDetails?.firstOrNull()?.offerToken?.let {
                                    setOfferToken(it)
                                }
                            }
                        }.build(),
                )

            val flowParams =
                BillingFlowParams
                    .newBuilder()
                    .setProductDetailsParamsList(productDetailsParamsList)
                    .build()

            val result = billingClient.launchBillingFlow(activity, flowParams)
            if (result.responseCode != BillingClient.BillingResponseCode.OK) {
                trackPurchaseResult(
                    success = false,
                    source = MonetizationSources.PAYWALL,
                    entryPoint = entryPoint,
                    responseCode = result.responseCode,
                    debugMessage = result.debugMessage,
                )
                pendingPurchaseEntryPoint = null
                return false
            }
            return true
        }

        private suspend fun fetchAllProductDetails() {
            fetchProductDetails(BASE_PRODUCT_ID)
            fetchProductDetails(ELITE_PRODUCT_ID)
        }

        private suspend fun fetchProductDetails(productID: String): com.android.billingclient.api.ProductDetails? {
            val productType =
                if (productID == ELITE_PRODUCT_ID) {
                    BillingClient.ProductType.SUBS
                } else {
                    BillingClient.ProductType.INAPP
                }

            val productList =
                listOf(
                    QueryProductDetailsParams.Product
                        .newBuilder()
                        .setProductId(productID)
                        .setProductType(productType)
                        .build(),
                )

            val params =
                QueryProductDetailsParams
                    .newBuilder()
                    .setProductList(productList)
                    .build()

            val result = billingClient.queryProductDetails(params)
            val details = result.productDetailsList?.firstOrNull()
            if (details != null) {
                cachedProductDetails[productID] = details
            }
            return details
        }

        suspend fun getFormattedPrice(productID: String): String {
            val details = cachedProductDetails[productID] ?: fetchProductDetails(productID)
            return if (productID == ELITE_PRODUCT_ID) {
                details
                    ?.subscriptionOfferDetails
                    ?.firstOrNull()
                    ?.pricingPhases
                    ?.pricingPhaseList
                    ?.firstOrNull()
                    ?.formattedPrice ?: "$19.99"
            } else {
                details?.oneTimePurchaseOfferDetails?.formattedPrice ?: "$4.99"
            }
        }

        override fun onPurchasesUpdated(
            result: BillingResult,
            purchases: MutableList<Purchase>?,
        ) {
            var hasPurchased = false
            if (result.responseCode == BillingClient.BillingResponseCode.OK && purchases != null) {
                for (purchase in purchases) {
                    if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
                        hasPurchased = true
                        updateEntitlementFromPurchase(purchase)
                        externalScope.launch { acknowledgePurchaseIfNeeded(purchase) }
                    }
                }
            }
            trackPurchaseResult(
                success = hasPurchased,
                source = if (pendingPurchaseEntryPoint.isNullOrBlank()) MonetizationSources.BILLING_CALLBACK else MonetizationSources.PAYWALL,
                entryPoint = pendingPurchaseEntryPoint,
                responseCode = result.responseCode,
                debugMessage = result.debugMessage,
            )
            pendingPurchaseEntryPoint = null
        }

        private fun updateEntitlementFromPurchase(purchase: Purchase) {
            if (purchase.products.contains(ELITE_PRODUCT_ID)) {
                _entitlementLevel.value = EntitlementLevel.ELITE
            } else if (purchase.products.contains(BASE_PRODUCT_ID)) {
                if (_entitlementLevel.value == EntitlementLevel.NONE) {
                    _entitlementLevel.value = EntitlementLevel.BASE
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

        suspend fun restorePurchasesFromPaywall(entryPoint: String): Boolean =
            restorePurchases(
                source = MonetizationSources.PAYWALL,
                entryPoint = entryPoint,
                trackResult = true,
            )

        private fun trackPurchaseResult(
            success: Boolean,
            source: String,
            entryPoint: String?,
            responseCode: Int,
            debugMessage: String?,
        ) {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_PURCHASE_RESULT,
                MonetizationAnalyticsPayload.resultProperties(
                    success = success,
                    result = purchaseResultValue(success, responseCode),
                    source = source,
                    entryPoint = entryPoint,
                    responseCode = responseCode,
                    debugMessage = debugMessage,
                ),
            )
        }

        private fun trackRestoreResult(
            success: Boolean,
            source: String,
            entryPoint: String?,
            responseCode: Int,
            debugMessage: String?,
        ) {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_RESTORE_RESULT,
                MonetizationAnalyticsPayload.resultProperties(
                    success = success,
                    result = restoreResultValue(success),
                    source = source,
                    entryPoint = entryPoint,
                    responseCode = responseCode,
                    debugMessage = debugMessage,
                ),
            )
        }

        private fun purchaseResultValue(
            success: Boolean,
            responseCode: Int,
        ): String =
            when {
                success -> "success"
                responseCode == BillingClient.BillingResponseCode.USER_CANCELED -> "cancelled"
                else -> "failed"
            }

        private fun restoreResultValue(success: Boolean): String = if (success) "restored" else "failed"

        fun forcePro() {
            _entitlementLevel.value = EntitlementLevel.ELITE
            context
                .getSharedPreferences("pro_prefs", Context.MODE_PRIVATE)
                .edit()
                .putBoolean("forced_pro", true)
                .apply()
            analyticsService.track("dev_force_pro", emptyMap())
        }

        // Feature gates
        fun maxSecondsLimit(level: EntitlementLevel = _entitlementLevel.value): Int =
            if (level.isPro) TimerConfig.MAX_SECONDS_PRO else TimerConfig.MAX_SECONDS_FREE

        fun availableSounds(level: EntitlementLevel = _entitlementLevel.value): List<SoundType> =
            if (level.isPro) SoundType.entries.toList() else SoundType.FREE

        fun unlockProForDebug(entryPoint: String): Boolean {
            if (!canUseDebugUnlock()) {
                return false
            }
            _entitlementLevel.value = EntitlementLevel.ELITE
            trackPurchaseResult(
                success = true,
                source = MonetizationSources.PAYWALL,
                entryPoint = entryPoint,
                responseCode = BillingClient.BillingResponseCode.OK,
                debugMessage = "debug_override",
            )
            return true
        }
    }

internal object MonetizationSources {
    const val PAYWALL = "paywall"
    const val AUTO_RESTORE = "auto_restore"
    const val BILLING_CALLBACK = "billing_callback"
}

internal object MonetizationAnalyticsPayload {
    fun resultProperties(
        success: Boolean,
        result: String,
        source: String,
        entryPoint: String?,
        responseCode: Int,
        debugMessage: String?,
    ): Map<String, Any> =
        mapOf(
            AnalyticsProperties.RESULT to result,
            AnalyticsProperties.SUCCESS to success,
            AnalyticsProperties.SOURCE to source,
            AnalyticsProperties.ENTRY_POINT to (entryPoint ?: source),
            AnalyticsProperties.RESPONSE_CODE to responseCode,
            AnalyticsProperties.DEBUG_MESSAGE to (debugMessage ?: ""),
        )
}
