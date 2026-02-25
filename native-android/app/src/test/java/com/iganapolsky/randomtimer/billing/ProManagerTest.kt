package com.iganapolsky.randomtimer.billing

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.ProductDetailsResult
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesResult
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import com.android.billingclient.api.acknowledgePurchase
import com.android.billingclient.api.queryProductDetails
import com.android.billingclient.api.queryPurchasesAsync
import com.google.common.truth.Truth.assertThat
import io.mockk.clearAllMocks
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.just
import io.mockk.mockk
import io.mockk.mockkStatic
import io.mockk.runs
import io.mockk.slot
import io.mockk.verify
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ProManagerTest {
    private val testDispatcher = StandardTestDispatcher()

    private lateinit var context: Context
    private lateinit var activity: Activity
    private lateinit var billingClient: BillingClient
    private lateinit var billingClientBuilder: BillingClient.Builder
    private lateinit var productDetailsParamsBuilder: BillingFlowParams.ProductDetailsParams.Builder
    private lateinit var productDetailsParams: BillingFlowParams.ProductDetailsParams
    private lateinit var billingFlowParamsBuilder: BillingFlowParams.Builder
    private lateinit var billingFlowParams: BillingFlowParams
    private val connectionListener = slot<BillingClientStateListener>()

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)

        context = mockk(relaxed = true)
        activity = mockk(relaxed = true)
        billingClient = mockk(relaxed = true)
        billingClientBuilder = mockk(relaxed = true)
        productDetailsParamsBuilder = mockk(relaxed = true)
        productDetailsParams = mockk(relaxed = true)
        billingFlowParamsBuilder = mockk(relaxed = true)
        billingFlowParams = mockk(relaxed = true)

        mockkStatic(BillingClient::class)
        mockkStatic(BillingFlowParams::class)
        mockkStatic(BillingFlowParams.ProductDetailsParams::class)
        every { BillingClient.newBuilder(context) } returns billingClientBuilder
        every { BillingFlowParams.ProductDetailsParams.newBuilder() } returns productDetailsParamsBuilder
        every { productDetailsParamsBuilder.setProductDetails(any()) } returns productDetailsParamsBuilder
        every { productDetailsParamsBuilder.build() } returns productDetailsParams
        every { BillingFlowParams.newBuilder() } returns billingFlowParamsBuilder
        every { billingFlowParamsBuilder.setProductDetailsParamsList(any()) } returns billingFlowParamsBuilder
        every { billingFlowParamsBuilder.build() } returns billingFlowParams
        every { billingClientBuilder.setListener(any()) } returns billingClientBuilder
        every { billingClientBuilder.enablePendingPurchases(any()) } returns billingClientBuilder
        every { billingClientBuilder.build() } returns billingClient
        every { billingClient.startConnection(capture(connectionListener)) } just runs
        every { billingClient.launchBillingFlow(any(), billingFlowParams) } returns billingResult(BillingClient.BillingResponseCode.OK)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
        clearAllMocks()
        io.mockk.unmockkAll()
    }

    @Test
    fun `launchPurchase returns false and reconnects when billing client is not ready`() =
        runTest {
            every { billingClient.isReady } returns false
            val manager = ProManager(context)

            val launched = manager.launchPurchase(activity)

            assertThat(launched).isFalse()
            verify(exactly = 2) { billingClient.startConnection(any()) }
            verify(exactly = 0) { billingClient.launchBillingFlow(any(), any()) }
        }

    @Test
    fun `launchPurchase uses cached details and returns true for OK billing flow response`() =
        runTest {
            every { billingClient.isReady } returns true
            val manager = ProManager(context)
            setCachedProductDetails(manager, mockLaunchableProductDetails())

            val launched = manager.launchPurchase(activity)

            assertThat(launched).isTrue()
            verify(exactly = 1) { billingClient.launchBillingFlow(activity, any()) }
        }

    @Test
    fun `launchPurchase returns false when billing flow response is not OK`() =
        runTest {
            every { billingClient.isReady } returns true
            every {
                billingClient.launchBillingFlow(any(), billingFlowParams)
            } returns billingResult(BillingClient.BillingResponseCode.USER_CANCELED)
            val manager = ProManager(context)
            setCachedProductDetails(manager, mockLaunchableProductDetails())

            val launched = manager.launchPurchase(activity)

            assertThat(launched).isFalse()
        }

    @Test
    fun `connectAndRestore marks pro when purchased pro product is restored`() =
        runTest {
            mockkStatic("com.android.billingclient.api.BillingClientKotlinKt")
            every { billingClient.isReady } returns true
            val restoredPurchase =
                mockPurchase(
                    products = listOf(ProManager.PRODUCT_ID),
                    purchaseState = Purchase.PurchaseState.PURCHASED,
                    acknowledged = true,
                )
            coEvery { billingClient.queryPurchasesAsync(any<QueryPurchasesParams>()) } returns
                PurchasesResult(
                    billingResult(BillingClient.BillingResponseCode.OK),
                    listOf(restoredPurchase),
                )

            val manager = ProManager(context)
            connectionListener.captured.onBillingSetupFinished(billingResult(BillingClient.BillingResponseCode.OK))
            advanceUntilIdle()

            assertThat(manager.isPro.value).isTrue()
        }

    @Test
    fun `getFormattedPrice falls back to default when product details query is empty`() =
        runTest {
            mockkStatic("com.android.billingclient.api.BillingClientKotlinKt")
            val manager = ProManager(context)
            coEvery { billingClient.queryProductDetails(any<QueryProductDetailsParams>()) } returns
                ProductDetailsResult(
                    billingResult(BillingClient.BillingResponseCode.OK),
                    emptyList(),
                )

            val price = manager.getFormattedPrice()

            assertThat(price).isEqualTo("$4.99")
        }

    @Test
    fun `onPurchasesUpdated sets pro and acknowledges unacknowledged purchase`() =
        runTest {
            mockkStatic("com.android.billingclient.api.BillingClientKotlinKt")
            val manager = ProManager(context)
            val purchase =
                mockPurchase(
                    products = listOf(ProManager.PRODUCT_ID),
                    purchaseState = Purchase.PurchaseState.PURCHASED,
                    acknowledged = false,
                    token = "purchase-token",
                )
            coEvery { billingClient.acknowledgePurchase(any()) } returns billingResult(BillingClient.BillingResponseCode.OK)

            manager.onPurchasesUpdated(
                billingResult(BillingClient.BillingResponseCode.OK),
                mutableListOf(purchase),
            )
            advanceUntilIdle()

            assertThat(manager.isPro.value).isTrue()
            coVerify(exactly = 1) {
                billingClient.acknowledgePurchase(match { it.purchaseToken == "purchase-token" })
            }
        }

    @Test
    fun `onPurchasesUpdated ignores non purchased entries`() =
        runTest {
            mockkStatic("com.android.billingclient.api.BillingClientKotlinKt")
            val manager = ProManager(context)
            val pendingPurchase =
                mockPurchase(
                    products = listOf(ProManager.PRODUCT_ID),
                    purchaseState = Purchase.PurchaseState.PENDING,
                    acknowledged = false,
                )
            coEvery { billingClient.acknowledgePurchase(any()) } returns billingResult(BillingClient.BillingResponseCode.OK)

            manager.onPurchasesUpdated(
                billingResult(BillingClient.BillingResponseCode.OK),
                mutableListOf(pendingPurchase),
            )
            advanceUntilIdle()

            assertThat(manager.isPro.value).isFalse()
            coVerify(exactly = 0) { billingClient.acknowledgePurchase(any()) }
        }

    private fun mockPurchase(
        products: List<String>,
        purchaseState: Int,
        acknowledged: Boolean,
        token: String = "token-1",
    ): Purchase {
        val purchase = mockk<Purchase>()
        every { purchase.products } returns products
        every { purchase.purchaseState } returns purchaseState
        every { purchase.isAcknowledged } returns acknowledged
        every { purchase.purchaseToken } returns token
        return purchase
    }

    private fun setCachedProductDetails(
        manager: ProManager,
        details: ProductDetails?,
    ) {
        val field = ProManager::class.java.getDeclaredField("cachedProductDetails")
        field.isAccessible = true
        field.set(manager, details)
    }

    private fun mockLaunchableProductDetails(): ProductDetails = mockk(relaxed = true)

    private fun billingResult(responseCode: Int): BillingResult =
        BillingResult
            .newBuilder()
            .setResponseCode(responseCode)
            .setDebugMessage("test")
            .build()
}
