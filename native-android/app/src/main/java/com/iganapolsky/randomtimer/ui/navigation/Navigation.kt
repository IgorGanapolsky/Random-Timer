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
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.ui.screens.ActiveTimerScreen
import com.iganapolsky.randomtimer.ui.screens.PaywallSheet
import com.iganapolsky.randomtimer.ui.screens.TimerSetupScreen
import com.iganapolsky.randomtimer.ui.viewmodel.TimerViewModel
import kotlinx.coroutines.launch

sealed class Screen(
    val route: String,
) {
    data object Setup : Screen("setup")

    data object ActiveTimer : Screen("active_timer")
}

@Composable
fun RandomTimerNavHost(
    navController: NavHostController = rememberNavController(),
    viewModel: TimerViewModel = hiltViewModel(),
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
    var paywallEntryPoint by remember { mutableStateOf("setup_upgrade_cta") }
    var paywallFreeTrialByProductId by remember { mutableStateOf<Map<String, Boolean>>(emptyMap()) }

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
                hasCompletedFirstTimer = viewModel.hasCompletedFirstTimer,
                isPro = isPro,
                isElite = isElite,
                onUpgradeTap = { feature ->
                    if (!viewModel.hasCompletedFirstTimer) {
                        viewModel.trackPaywallGateFirstTimer(feature)
                        android.widget.Toast
                            .makeText(
                                context,
                                "Complete your first drill to unlock Pro features.",
                                android.widget.Toast.LENGTH_LONG,
                            ).show()
                    } else {
                        viewModel.trackFeatureGateHit(feature)
                        scope.launch {
                            proPrice = viewModel.proManager.getFormattedPrice(ProManager.PRO_PRODUCT_ID)
                            monthlyPrice = viewModel.proManager.getFormattedMonthlyPrice()
                            paywallEntryPoint = "setup_upgrade_cta"
                            paywallFreeTrialByProductId =
                                mapOf(
                                    ProManager.MONTHLY_PRODUCT_ID to
                                        viewModel.proManager.hasFreeTrialOffer(ProManager.MONTHLY_PRODUCT_ID),
                                    ProManager.ELITE_PRODUCT_ID to
                                        viewModel.proManager.hasFreeTrialOffer(ProManager.ELITE_PRODUCT_ID),
                                )
                            showPaywall = true
                        }
                    }
                },
                onFeatureGateHit = { feature ->
                    viewModel.trackFeatureGateHit(feature)
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
                    onStop = {
                        viewModel.cancelTimer()
                    },
                    onDismissAlarm = {
                        viewModel.dismissAlarm()
                    },
                    onSilence = viewModel::silenceAlarm,
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

    LaunchedEffect(showPaywall, paywallEntryPoint) {
        if (showPaywall) {
            viewModel.trackPaywallViewed(paywallEntryPoint)
        }
    }

    if (showPaywall) {
        PaywallSheet(
            proPrice = proPrice,
            monthlyPrice = monthlyPrice,
            freeTrialByProductId = paywallFreeTrialByProductId,
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
                    // Only dismiss if billing dialog launched (user will see Google Play sheet)
                    // The actual purchase result comes via onPurchasesUpdated callback
                    if (launched) {
                        showPaywall = false
                    }
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
