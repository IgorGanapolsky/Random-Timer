package com.iganapolsky.randomtimer.ui.navigation

import android.app.Activity
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsScreens
import com.iganapolsky.randomtimer.analytics.PaywallValueFraming
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.monetization.QualifiedTrainingPaywallPolicy
import com.iganapolsky.randomtimer.monetization.QualifiedTrainingPaywallStore
import com.iganapolsky.randomtimer.ui.screens.ActiveTimerScreen
import com.iganapolsky.randomtimer.ui.screens.PaywallSheet
import com.iganapolsky.randomtimer.ui.screens.TimerSetupScreen
import com.iganapolsky.randomtimer.ui.viewmodel.TimerViewModel
import kotlinx.coroutines.launch
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

sealed class Screen(
    val route: String,
) {
    data object Setup : Screen("setup")

    data object ActiveTimer : Screen("active_timer")
}

internal fun paywallEntryPointForFeature(feature: String): String =
    when (feature) {
        "setup_upgrade_cta" -> "setup_upgrade_cta"
        "extended_range" -> "range_gate"
        "voice_callouts" -> "voice_gate"
        "repeat_loop" -> "repeat_gate"
        "pro_sounds" -> "sound_arsenal_gate"
        QualifiedTrainingPaywallPolicy.FEATURE_GATE -> QualifiedTrainingPaywallPolicy.ENTRY_POINT
        else -> "unknown"
    }

@Composable
fun RandomTimerNavHost(
    navController: NavHostController = rememberNavController(),
    viewModel: TimerViewModel = hiltViewModel(),
    pendingDeepLinkUri: String? = null,
) {
    val config by viewModel.config.collectAsStateWithLifecycle()
    val timerState by viewModel.timerState.collectAsStateWithLifecycle()
    val isPro by viewModel.proManager.isPro.collectAsStateWithLifecycle()
    val isElite by viewModel.proManager.isElite.collectAsStateWithLifecycle()
    val currentRoute =
        navController
            .currentBackStackEntryAsState()
            .value
            ?.destination
            ?.route
    val context = LocalContext.current
    val activity = context as? Activity
    val scope = rememberCoroutineScope()
    var showPaywall by remember { mutableStateOf(false) }
    var proPrice by remember { mutableStateOf("$29.99") }
    var monthlyPrice by remember { mutableStateOf("$3.99") }
    var lifetimePrice by remember { mutableStateOf("$4.99") }
    var paywallEntryPoint by remember { mutableStateOf("unknown") }
    var paywallTrialEligibilityByProductId by remember { mutableStateOf(emptyMap<String, Boolean>()) }
    var paywallAvailableProductIds by remember { mutableStateOf(emptySet<String>()) }
    var paywallBillingCatalogProbed by remember { mutableStateOf(false) }
    var paywallDefaultToAnnual by remember { mutableStateOf(false) }
    var paywallValueFramingVariant by remember { mutableStateOf(PaywallValueFraming.CONTROL) }
    val qualifiedTrainingPaywallStore = remember { QualifiedTrainingPaywallStore(context) }

    fun presentPaywallForFeature(feature: String) {
        viewModel.trackFeatureGateHit(feature)
        scope.launch {
            proPrice = viewModel.proManager.getFormattedPrice(ProManager.PRO_PRODUCT_ID)
            monthlyPrice = viewModel.proManager.getFormattedMonthlyPrice()
            lifetimePrice = viewModel.proManager.getFormattedPrice(ProManager.BASE_PRODUCT_ID)
            paywallAvailableProductIds = viewModel.proManager.availablePaywallProductIds()
            paywallBillingCatalogProbed = true
            paywallEntryPoint = paywallEntryPointForFeature(feature)
            paywallTrialEligibilityByProductId =
                mapOf(
                    ProManager.MONTHLY_PRODUCT_ID to
                        viewModel.proManager.hasFreeTrialOffer(ProManager.MONTHLY_PRODUCT_ID),
                    ProManager.ELITE_PRODUCT_ID to
                        viewModel.proManager.hasFreeTrialOffer(ProManager.ELITE_PRODUCT_ID),
                )
            paywallDefaultToAnnual =
                suspendCoroutine { cont ->
                    viewModel.resolvePaywallDefaultAnnualExperiment { enabled ->
                        cont.resume(enabled)
                    }
                }
            paywallValueFramingVariant = viewModel.paywallValueFramingVariant()
            showPaywall = true
        }
    }

    LaunchedEffect(pendingDeepLinkUri, isPro) {
        val monetizationTarget = monetizationDeepLinkFromUri(pendingDeepLinkUri)
        if (monetizationTarget != null && !isPro) {
            presentPaywallForFeature(monetizationTarget.feature)
        }
    }

    // Auto-navigate based on timer state
    LaunchedEffect(timerState, currentRoute) {
        if (timerState != null) {
            // Timer is running - go to active timer screen
            if (currentRoute != Screen.ActiveTimer.route) {
                navController.navigate(Screen.ActiveTimer.route) {
                    launchSingleTop = true
                }
            }
        } else {
            // Timer stopped - go back to setup screen
            if (currentRoute == Screen.ActiveTimer.route) {
                val popped = navController.popBackStack(Screen.Setup.route, inclusive = false)
                if (!popped) {
                    navController.navigate(Screen.Setup.route) {
                        launchSingleTop = true
                        popUpTo(Screen.ActiveTimer.route) { inclusive = true }
                    }
                }
                // Prompt for review after timer completion (if eligible)
                activity?.let { viewModel.storeReviewManager.requestReview(it) }
            }
        }
    }

    LaunchedEffect(timerState, currentRoute, isPro, viewModel.totalSessions) {
        if (
            timerState == null &&
                currentRoute == Screen.Setup.route &&
                QualifiedTrainingPaywallPolicy.shouldPresent(
                    completedSessionCount = viewModel.totalSessions,
                    isPro = isPro,
                    alreadyPresented = qualifiedTrainingPaywallStore.hasPresented(),
                )
        ) {
            viewModel.trackQualifiedTrainingPaywallEligible(viewModel.totalSessions)
            qualifiedTrainingPaywallStore.markPresented()
            presentPaywallForFeature(QualifiedTrainingPaywallPolicy.FEATURE_GATE)
        }
    }

    NavHost(
        navController = navController,
        startDestination = Screen.Setup.route,
    ) {
        composable(
            Screen.Setup.route,
            enterTransition = { fadeIn(animationSpec = tween(300)) },
            exitTransition = {
                fadeOut(animationSpec = tween(300)) +
                    slideOutVertically(animationSpec = tween(300)) { it / 4 }
            },
            popEnterTransition = { fadeIn(animationSpec = tween(300)) },
            popExitTransition = { fadeOut(animationSpec = tween(300)) },
        ) {
            LaunchedEffect(Unit) {
                viewModel.trackScreen(AnalyticsScreens.TIMER_SETUP)
            }
            val setupEnterTimeMs = remember { System.currentTimeMillis() }
            DisposableEffect(Unit) {
                onDispose {
                    val dwellSeconds = (System.currentTimeMillis() - setupEnterTimeMs) / 1000.0
                    viewModel.trackScreenDwellTime("timer_setup", dwellSeconds)
                }
            }
            TimerSetupScreen(
                config = config,
                onConfigChange = viewModel::updateConfig,
                onStartTimer = viewModel::startTimer,
                onSoundPreview = viewModel::previewSound,
                onVolumePreview = viewModel::previewVolume,
                onCommandCuePreview = viewModel::previewCommandCue,
                totalSessions = viewModel.totalSessions,
                currentStreak = viewModel.currentStreak,
                isPro = isPro,
                isElite = isElite,
                onUpgradeTap = { feature ->
                    presentPaywallForFeature(feature)
                },
                onVoiceGenderSelected = { gender ->
                    viewModel.trackVoiceGenderSelected(gender)
                },
                onTrainingPresetApplied = { preset ->
                    viewModel.applyPresetAndStart(preset)
                },
                onVoiceGenderSelected = { gender ->
                    viewModel.trackVoiceGenderSelected(gender)
                },
                onSecretUnlock = {
                    viewModel.proManager.forcePro()
                },
            )
        }

        composable(
            Screen.ActiveTimer.route,
            enterTransition = {
                fadeIn(animationSpec = tween(300)) +
                    slideInVertically(animationSpec = tween(300)) { it / 4 }
            },
            exitTransition = { fadeOut(animationSpec = tween(300)) },
            popEnterTransition = { fadeIn(animationSpec = tween(300)) },
            popExitTransition = {
                fadeOut(animationSpec = tween(300)) +
                    slideOutVertically(animationSpec = tween(300)) { it / 4 }
            },
        ) {
            LaunchedEffect(Unit) {
                viewModel.trackScreen(AnalyticsScreens.ACTIVE_TIMER)
            }
            val state = timerState
            if (state == null) {
                LaunchedEffect(Unit) {
                    val popped = navController.popBackStack(Screen.Setup.route, inclusive = false)
                    if (!popped) {
                        navController.navigate(Screen.Setup.route) {
                            launchSingleTop = true
                            popUpTo(Screen.ActiveTimer.route) { inclusive = true }
                        }
                    }
                }
            } else {
                ActiveTimerScreen(
                    state = state,
                    isPro = isPro,
                    onStop = {
                        viewModel.cancelTimer()
                    },
                    onDismissAlarm = {
                        viewModel.dismissAlarm()
                    },
                    onPause = viewModel::pauseTimer,
                    onResume = viewModel::resumeTimer,
                    onReset = {
                        viewModel.resetTimer()
                    },
                    onLoopToggle = viewModel::updateLoopSetting,
                    onVoiceToggle = viewModel::updateVoiceSetting,
                )
            }
        }
    }

    LaunchedEffect(showPaywall, paywallEntryPoint, paywallDefaultToAnnual) {
        if (showPaywall) {
            viewModel.trackPaywallViewed(paywallEntryPoint, paywallDefaultToAnnual)
        }
    }

    LaunchedEffect(showPaywall, isPro) {
        if (showPaywall && isPro) {
            showPaywall = false
        }
    }

    if (showPaywall) {
        PaywallSheet(
            entryPoint = paywallEntryPoint,
            proPrice = proPrice,
            monthlyPrice = monthlyPrice,
            lifetimePrice = lifetimePrice,
            defaultToAnnualPlan = paywallDefaultToAnnual,
            valueFramingVariant = paywallValueFramingVariant,
            trialEligibilityByProductId = paywallTrialEligibilityByProductId,
            availableProductIds = paywallAvailableProductIds,
            billingCatalogProbed = paywallBillingCatalogProbed,
            onPlanSelected = { plan, productId, selectionSource ->
                viewModel.trackPaywallOfferSelected(
                    entryPoint = paywallEntryPoint,
                    productId = productId,
                    plan = plan,
                    selectionSource = selectionSource,
                )
            },
            onPurchase = { productID ->
                scope.launch {
                    val launched =
                        activity?.let {
                            viewModel.proManager.launchPurchase(it, productID, paywallEntryPoint)
                        } ?: false
                    if (!launched) {
                        // Purchase failed to launch — keep paywall open
                        // The billing dialog didn't appear, so user needs feedback
                        android.widget.Toast
                            .makeText(
                                activity ?: return@launch,
                                "Purchase unavailable. Please try again later.",
                                android.widget.Toast.LENGTH_LONG,
                            ).show()
                    }
                    // Keep the sheet open until entitlement changes so cancellation/errors can retry.
                }
            },
            onDebugUnlock = {
                if (viewModel.proManager.unlockProForDebug(paywallEntryPoint)) {
                    showPaywall = false
                }
            },
            onRestore = {
                scope.launch {
                    val restored = viewModel.proManager.restorePurchasesFromPaywall(paywallEntryPoint)
                    if (restored) {
                        showPaywall = false
                    }
                }
            },
            onDismiss = {
                viewModel.trackPaywallDismissed(paywallEntryPoint)
                showPaywall = false
            },
        )
    }
}
