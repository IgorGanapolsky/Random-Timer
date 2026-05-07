package com.iganapolsky.randomtimer.billing

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.AcknowledgePurchaseParams
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import com.android.billingclient.api.acknowledgePurchase
import com.android.billingclient.api.queryProductDetails
import com.android.billingclient.api.queryPurchasesAsync
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsProperties
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.analytics.SubscriptionFunnelSteps
import com.iganapolsky.randomtimer.domain.model.EntitlementLevel
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.service.ProAudioPackStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
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
        private val packStore: ProAudioPackStore,
        private val externalScope: CoroutineScope,
    ) : PurchasesUpdatedListener {
        companion object {
            const val BASE_PRODUCT_ID = "pro_base"
            const val ELITE_PRODUCT_ID = "elite_tactical"
            const val PRO_PRODUCT_ID = ELITE_PRODUCT_ID

            /** Monthly subscription: $3.99/month. Must be created in Google Play Console as a
             *  subscription product with billing period P1M under the same base plan as ELITE. */
            const val MONTHLY_PRODUCT_ID = "elite_tactical_monthly"

            internal fun canUseDebugUnlock(
                @Suppress("UNUSED_PARAMETER") isDebugBuild: Boolean = true,
            ): Boolean = true
        }

        private val _entitlementLevel = MutableStateFlow(EntitlementLevel.NONE)
        val entitlementLevel: StateFlow<EntitlementLevel> = _entitlementLevel.asStateFlow()
        private var debugOverrideActive = false

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

        /** Captures the exact trial offer submitted to Google Play for the pending flow. */
        private var pendingPurchaseFreeTrialProductId: String? = null
        private var pendingPurchaseFreeTrialOfferToken: String? = null

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
                        externalScope.launch {
                            delay(1000)
                            connectAndRestore()
                        }
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
                    (
                        purchase.products.contains(ELITE_PRODUCT_ID) ||
                            purchase.products.contains(MONTHLY_PRODUCT_ID)
                    ) &&
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
            if (level.isPro) {
                packStore.refreshIfNeeded(isPro = true)
            }

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
            clearPendingTrialOffer()
            if (!ensureBillingReadyForPurchase()) {
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

            val selectedOffer =
                when (productID) {
                    ELITE_PRODUCT_ID ->
                        selectSubscriptionOfferByPeriod(productDetails.toSubscriptionOffers(), "P1Y")
                    MONTHLY_PRODUCT_ID ->
                        selectSubscriptionOfferByPeriod(productDetails.toSubscriptionOffers(), "P1M")
                    else -> null
                }
            if ((productID == ELITE_PRODUCT_ID || productID == MONTHLY_PRODUCT_ID) && selectedOffer == null) {
                trackPurchaseResult(
                    success = false,
                    source = MonetizationSources.PAYWALL,
                    entryPoint = entryPoint,
                    responseCode = BillingClient.BillingResponseCode.ITEM_UNAVAILABLE,
                    debugMessage = "subscription_offer_unavailable",
                )
                pendingPurchaseEntryPoint = null
                return false
            }

            val selectedFreeTrialOfferToken = selectedOffer?.offerToken?.takeIf { selectedOffer.hasFreeTrial }
            pendingPurchaseFreeTrialProductId = productID.takeIf { selectedFreeTrialOfferToken != null }
            pendingPurchaseFreeTrialOfferToken = selectedFreeTrialOfferToken

            val productDetailsParamsList =
                listOf(
                    BillingFlowParams.ProductDetailsParams
                        .newBuilder()
                        .setProductDetails(productDetails)
                        .apply {
                            if (selectedOffer != null) {
                                setOfferToken(selectedOffer.offerToken)
                            }
                        }.build(),
                )

            val flowParams =
                BillingFlowParams
                    .newBuilder()
                    .setProductDetailsParamsList(productDetailsParamsList)
                    .build()

            analyticsService.track(
                AnalyticsEvents.PAYWALL_PURCHASE_ATTEMPT,
                mapOf(
                    "product_id" to productID,
                    AnalyticsProperties.SOURCE to MonetizationSources.PAYWALL,
                    AnalyticsProperties.ENTRY_POINT to entryPoint,
                    "has_free_trial" to (selectedFreeTrialOfferToken != null),
                ),
            )
            analyticsService.trackSubscriptionFunnelStep(
                SubscriptionFunnelSteps.PURCHASE_FLOW_LAUNCHED,
                mapOf(
                    AnalyticsProperties.PRODUCT_ID to productID,
                    "has_free_trial" to (selectedFreeTrialOfferToken != null),
                ),
            )
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
                clearPendingTrialOffer()
                return false
            }
            return true
        }

        private suspend fun ensureBillingReadyForPurchase(): Boolean {
            if (billingClient.isReady) {
                return true
            }
            connectAndRestore()
            repeat(6) {
                delay(500)
                if (billingClient.isReady) {
                    return true
                }
            }
            return billingClient.isReady
        }

        private suspend fun fetchAllProductDetails() {
            fetchProductDetails(BASE_PRODUCT_ID)
            fetchProductDetails(ELITE_PRODUCT_ID)
            fetchProductDetails(MONTHLY_PRODUCT_ID)
        }

        private suspend fun fetchProductDetails(productID: String): com.android.billingclient.api.ProductDetails? {
            val productType =
                if (productID == ELITE_PRODUCT_ID || productID == MONTHLY_PRODUCT_ID) {
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
            } else {
                analyticsService.track(
                    "billing_product_not_found",
                    mapOf(
                        "product_id" to productID,
                        "billing_ready" to billingClient.isReady,
                    ),
                )
            }
            return details
        }

        /**
         * Fetches product details before checking trial availability so launch-time cache races
         * do not hide valid free-trial CTAs for the selected plan.
         */
        suspend fun hasFreeTrialOffer(productID: String): Boolean {
            val details = cachedProductDetails[productID] ?: fetchProductDetails(productID) ?: return false
            val billingPeriod =
                when (productID) {
                    ELITE_PRODUCT_ID -> "P1Y"
                    MONTHLY_PRODUCT_ID -> "P1M"
                    else -> return false
                }
            return selectSubscriptionOfferByPeriod(details.toSubscriptionOffers(), billingPeriod)?.hasFreeTrial == true
        }

        suspend fun hasFreeTrialOffer(): Boolean = hasFreeTrialOffer(ELITE_PRODUCT_ID)

        suspend fun getFormattedPrice(productID: String): String {
            val details = cachedProductDetails[productID] ?: fetchProductDetails(productID)
            return when (productID) {
                ELITE_PRODUCT_ID ->
                    selectSubscriptionOfferByPeriod(details?.toSubscriptionOffers().orEmpty(), "P1Y")
                        ?.displayPrice ?: "$29.99"
                MONTHLY_PRODUCT_ID ->
                    selectSubscriptionOfferByPeriod(details?.toSubscriptionOffers().orEmpty(), "P1M")
                        ?.displayPrice ?: "$3.99"
                else ->
                    details?.oneTimePurchaseOfferDetails?.formattedPrice ?: "$7.99"
            }
        }

        suspend fun getFormattedProPrice(): String = getFormattedPrice(PRO_PRODUCT_ID)

        suspend fun getFormattedMonthlyPrice(): String = getFormattedPrice(MONTHLY_PRODUCT_ID)

        /**
         * Returns the numeric price in the user's local currency from the cached ProductDetails.
         * Used to populate the "revenue" property on analytics events.
         * Falls back to known defaults if cache is empty (e.g. billing callback arrives before fetch).
         */
        private fun priceAmountFromCache(productID: String): Double {
            val details = cachedProductDetails[productID]
            return when (productID) {
                ELITE_PRODUCT_ID -> {
                    // Annual subscription: find P1Y offer token, pull priceAmountMicros from
                    // the raw Google billing PricingPhaseList (last/base phase, not any trial).
                    val preferredToken =
                        selectSubscriptionOfferByPeriod(
                            details?.toSubscriptionOffers().orEmpty(),
                            "P1Y",
                        )?.offerToken
                    val micros =
                        details
                            ?.subscriptionOfferDetails
                            ?.firstOrNull { it.offerToken == preferredToken }
                            ?.pricingPhases
                            ?.pricingPhaseList
                            ?.lastOrNull()
                            ?.priceAmountMicros
                            ?: 29_990_000L // fallback: $29.99
                    micros / 1_000_000.0
                }
                MONTHLY_PRODUCT_ID -> {
                    // Monthly subscription: find P1M offer token.
                    val preferredToken =
                        selectSubscriptionOfferByPeriod(
                            details?.toSubscriptionOffers().orEmpty(),
                            "P1M",
                        )?.offerToken
                    val micros =
                        details
                            ?.subscriptionOfferDetails
                            ?.firstOrNull { it.offerToken == preferredToken }
                            ?.pricingPhases
                            ?.pricingPhaseList
                            ?.lastOrNull()
                            ?.priceAmountMicros
                            ?: 3_990_000L // fallback: $3.99
                    micros / 1_000_000.0
                }
                else -> {
                    // One-time purchase
                    val micros = details?.oneTimePurchaseOfferDetails?.priceAmountMicros ?: 499_000L // fallback: $4.99
                    micros / 1_000_000.0
                }
            }
        }

        suspend fun launchProPurchase(
            activity: Activity,
            entryPoint: String,
        ): Boolean = launchPurchase(activity, PRO_PRODUCT_ID, entryPoint)

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
            // Track purchase_failed for non-success, non-cancellation outcomes
            if (!hasPurchased && result.responseCode != BillingClient.BillingResponseCode.USER_CANCELED) {
                val failedProductId = purchases?.firstOrNull()?.products?.firstOrNull() ?: "unknown"
                val reason =
                    when (result.responseCode) {
                        BillingClient.BillingResponseCode.SERVICE_DISCONNECTED -> "service_disconnected"
                        BillingClient.BillingResponseCode.ITEM_UNAVAILABLE -> "item_unavailable"
                        BillingClient.BillingResponseCode.ITEM_ALREADY_OWNED -> "item_already_owned"
                        BillingClient.BillingResponseCode.BILLING_UNAVAILABLE -> "billing_unavailable"
                        BillingClient.BillingResponseCode.ERROR -> "billing_error"
                        BillingClient.BillingResponseCode.NETWORK_ERROR -> "network_error"
                        else -> "unknown_${result.responseCode}"
                    }
                analyticsService.track(
                    AnalyticsEvents.PURCHASE_FAILED,
                    mapOf(
                        AnalyticsProperties.REASON to reason,
                        AnalyticsProperties.PRODUCT_ID to failedProductId,
                        AnalyticsProperties.RESPONSE_CODE to result.responseCode,
                        AnalyticsProperties.DEBUG_MESSAGE to (result.debugMessage ?: ""),
                    ),
                )
                analyticsService.track(
                    AnalyticsEvents.PAYWALL_PURCHASE_FAIL_REASON,
                    mapOf(
                        AnalyticsProperties.REASON to reason,
                        AnalyticsProperties.PRODUCT_ID to failedProductId,
                        AnalyticsProperties.ENTRY_POINT to (pendingPurchaseEntryPoint ?: ""),
                        AnalyticsProperties.RESPONSE_CODE to result.responseCode,
                        AnalyticsProperties.DEBUG_MESSAGE to (result.debugMessage ?: ""),
                    ),
                )
            }
            if (hasPurchased) {
                val purchasedProductId = purchases?.firstOrNull()?.products?.firstOrNull() ?: ""
                val revenueAmount = priceAmountFromCache(purchasedProductId)
                analyticsService.track(
                    AnalyticsEvents.PAYWALL_PURCHASE_SUCCESS,
                    mapOf(
                        AnalyticsProperties.SOURCE to
                            (if (pendingPurchaseEntryPoint.isNullOrBlank()) MonetizationSources.BILLING_CALLBACK else MonetizationSources.PAYWALL),
                        AnalyticsProperties.ENTRY_POINT to (pendingPurchaseEntryPoint ?: ""),
                        AnalyticsProperties.ENTITLEMENT_LEVEL to _entitlementLevel.value.name.lowercase(),
                        AnalyticsProperties.PRODUCT_ID to purchasedProductId,
                        AnalyticsProperties.REVENUE to revenueAmount,
                    ),
                )
                // Google Play's Purchase object does not expose a store-confirmed trial flag.
                // Emit this only when the completed purchase matches the trial offer token we launched.
                if (purchaseMatchesPendingTrialOffer(purchasedProductId)) {
                    analyticsService.track(
                        AnalyticsEvents.FREE_TRIAL_STARTED,
                        mapOf(
                            AnalyticsProperties.PRODUCT_ID to purchasedProductId,
                            AnalyticsProperties.ENTRY_POINT to (pendingPurchaseEntryPoint ?: ""),
                            AnalyticsProperties.TRIAL_VERIFICATION_SOURCE to "google_play_selected_offer",
                            AnalyticsProperties.TRIAL_VERIFIED to false,
                        ),
                    )
                    analyticsService.trackSubscriptionFunnelStep(
                        SubscriptionFunnelSteps.TRIAL_STARTED,
                        mapOf(AnalyticsProperties.PRODUCT_ID to purchasedProductId),
                    )
                }
                analyticsService.trackSubscriptionFunnelStep(
                    SubscriptionFunnelSteps.PURCHASE_SUCCEEDED,
                    mapOf(AnalyticsProperties.PRODUCT_ID to purchasedProductId),
                )
            }
            trackPurchaseResult(
                success = hasPurchased,
                source = if (pendingPurchaseEntryPoint.isNullOrBlank()) MonetizationSources.BILLING_CALLBACK else MonetizationSources.PAYWALL,
                entryPoint = pendingPurchaseEntryPoint,
                responseCode = result.responseCode,
                debugMessage = result.debugMessage,
            )
            pendingPurchaseEntryPoint = null
            clearPendingTrialOffer()
        }

        private fun purchaseMatchesPendingTrialOffer(purchasedProductId: String): Boolean =
            purchasedProductId.isNotBlank() &&
                purchasedProductId == pendingPurchaseFreeTrialProductId &&
                pendingPurchaseFreeTrialOfferToken != null

        private fun clearPendingTrialOffer() {
            pendingPurchaseFreeTrialProductId = null
            pendingPurchaseFreeTrialOfferToken = null
        }

        private fun updateEntitlementFromPurchase(purchase: Purchase) {
            if (purchase.products.contains(ELITE_PRODUCT_ID) ||
                purchase.products.contains(MONTHLY_PRODUCT_ID)
            ) {
                _entitlementLevel.value = EntitlementLevel.ELITE
            } else if (purchase.products.contains(BASE_PRODUCT_ID)) {
                if (_entitlementLevel.value == EntitlementLevel.NONE) {
                    _entitlementLevel.value = EntitlementLevel.BASE
                }
            }
            if (_entitlementLevel.value.isPro) {
                packStore.refreshIfNeeded(isPro = true)
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
            // Cycle: NONE → BASE → ELITE → NONE
            val next =
                when (_entitlementLevel.value) {
                    EntitlementLevel.NONE -> EntitlementLevel.BASE
                    EntitlementLevel.BASE -> EntitlementLevel.ELITE
                    EntitlementLevel.ELITE -> EntitlementLevel.NONE
                }
            _entitlementLevel.value = next
            if (next.isPro) {
                packStore.refreshIfNeeded(isPro = true)
            }
            context
                .getSharedPreferences("pro_prefs", Context.MODE_PRIVATE)
                .edit()
                .putBoolean("forced_pro", next != EntitlementLevel.NONE)
                .putString("forced_level", next.name)
                .apply()
            analyticsService.track("dev_force_pro", mapOf("level" to next.name))
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
            debugOverrideActive = true
            _entitlementLevel.value = EntitlementLevel.ELITE
            packStore.refreshIfNeeded(isPro = true)
            analyticsService.track(
                "dev_debug_unlock",
                mapOf(
                    "entry_point" to entryPoint,
                    "is_developer_action" to true,
                ),
            )
            return true
        }
    }

internal data class SubscriptionPricingPhase(
    val formattedPrice: String,
    val billingPeriod: String,
    /** True when priceAmountMicros == 0, indicating a free trial phase. */
    val isFree: Boolean = false,
)

internal data class SubscriptionOffer(
    val offerToken: String,
    val pricingPhases: List<SubscriptionPricingPhase>,
) {
    val displayPrice: String?
        get() = pricingPhases.lastOrNull()?.formattedPrice ?: pricingPhases.firstOrNull()?.formattedPrice

    /** True when the offer contains at least one zero-price (free trial) phase. */
    val hasFreeTrial: Boolean
        get() = pricingPhases.any { it.isFree }
}

/** Selects the subscription offer that matches a specific ISO 8601 billing period (e.g. "P1Y", "P1M"). */
internal fun selectSubscriptionOfferByPeriod(
    offers: List<SubscriptionOffer>,
    period: String,
): SubscriptionOffer? = offers.firstOrNull { offer -> offer.pricingPhases.any { it.billingPeriod == period } }

/**
 * Select the best offer to present to the user.
 * Priority: free-trial offer > annual offer > first available offer.
 */
internal fun selectPreferredSubscriptionOffer(offers: List<SubscriptionOffer>): SubscriptionOffer? =
    offers.firstOrNull { it.hasFreeTrial }
        ?: selectSubscriptionOfferByPeriod(offers, "P1Y")
        ?: offers.firstOrNull()

private fun com.android.billingclient.api.ProductDetails.toSubscriptionOffers(): List<SubscriptionOffer> =
    subscriptionOfferDetails
        ?.map { offer ->
            SubscriptionOffer(
                offerToken = offer.offerToken,
                pricingPhases =
                    offer.pricingPhases.pricingPhaseList.map { phase ->
                        SubscriptionPricingPhase(
                            formattedPrice = phase.formattedPrice,
                            billingPeriod = phase.billingPeriod,
                            isFree = phase.priceAmountMicros == 0L,
                        )
                    },
            )
        }.orEmpty()

internal object MonetizationSources {
    const val PAYWALL = "paywall"
    const val AUTO_RESTORE = "auto_restore"
    const val BILLING_CALLBACK = "billing_callback"
}

internal object MonetizationAnalyticsPayload {
    fun attemptProperties(
        source: String,
        entryPoint: String?,
        productID: String,
    ): Map<String, Any> =
        mapOf(
            AnalyticsProperties.SOURCE to source,
            AnalyticsProperties.ENTRY_POINT to (entryPoint ?: source),
            AnalyticsProperties.PRODUCT_ID to productID,
        )

    fun successProperties(
        source: String,
        entryPoint: String?,
        productID: String?,
        responseCode: Int,
        debugMessage: String?,
    ): Map<String, Any> =
        buildMap {
            put(AnalyticsProperties.SOURCE, source)
            put(AnalyticsProperties.ENTRY_POINT, entryPoint ?: source)
            put(AnalyticsProperties.SUCCESS, true)
            put(AnalyticsProperties.RESPONSE_CODE, responseCode)
            put(AnalyticsProperties.DEBUG_MESSAGE, debugMessage ?: "")
            productID?.let { put(AnalyticsProperties.PRODUCT_ID, it) }
        }

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
