package com.iganapolsky.randomtimer.ui.navigation

import android.app.Activity
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.iganapolsky.randomtimer.ui.screens.ActiveTimerScreen
import com.iganapolsky.randomtimer.ui.screens.PaywallSheet
import com.iganapolsky.randomtimer.ui.screens.TimerSetupScreen
import com.iganapolsky.randomtimer.ui.viewmodel.TimerViewModel
import kotlinx.coroutines.launch

sealed class Screen(val route: String) {
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
    val currentRoute = navController.currentBackStackEntryAsState().value?.destination?.route
    val activity = LocalContext.current as? Activity
    val scope = rememberCoroutineScope()
    var showPaywall by remember { mutableStateOf(false) }
    var paywallPrice by remember { mutableStateOf("$4.99") }

    // Auto-navigate based on timer state
    LaunchedEffect(timerState, currentRoute) {
        if (timerState != null) {
            if (currentRoute != Screen.ActiveTimer.route) {
                navController.navigate(Screen.ActiveTimer.route) { launchSingleTop = true }
            }
        } else if (currentRoute == Screen.ActiveTimer.route) {
            navController.popBackStack(Screen.Setup.route, inclusive = false)
            activity?.let { viewModel.storeReviewManager.requestReview(it) }
        }
    }

    NavHost(navController = navController, startDestination = Screen.Setup.route) {
        composable(Screen.Setup.route) {
            TimerSetupScreen(
                config = config,
                onConfigChange = viewModel::updateConfig,
                onStartTimer = viewModel::startTimer,
                onSoundPreview = viewModel::previewSound,
                onVolumePreview = viewModel::previewVolume,
                totalSessions = viewModel.totalSessions,
                currentStreak = viewModel.currentStreak,
                hasCompletedFirstTimer = viewModel.hasCompletedFirstTimer,
                isPro = isPro,
                onUpgradeTap = {
                    scope.launch {
                        paywallPrice = viewModel.proManager.getFormattedPrice()
                        showPaywall = true
                    }
                },
                onSecretUnlock = {
                    // Backdoor
                    viewModel.forcePro()
                }
            )
        }

        composable(Screen.ActiveTimer.route) {
            val state = timerState
            if (state == null) {
                LaunchedEffect(Unit) { navController.popBackStack(Screen.Setup.route, inclusive = false) }
            } else {
                ActiveTimerScreen(
                    state = state,
                    onStop = { viewModel.cancelTimer() },
                    onDismissAlarm = { viewModel.dismissAlarm() },
                    onSilence = viewModel::silenceAlarm,
                    onPause = viewModel::pauseTimer,
                    onResume = viewModel::resumeTimer,
                    onReset = { viewModel.resetTimer() },
                    onLoopToggle = viewModel::updateLoopSetting,
                )
            }
        }
    }

    if (showPaywall) {
        PaywallSheet(
            price = paywallPrice,
            onPurchase = {
                activity?.let {
                    scope.launch {
                        viewModel.proManager.launchPurchase(it, "paywall")
                        showPaywall = false
                    }
                }
            },
            onRestore = {
                scope.launch {
                    viewModel.proManager.restorePurchasesFromPaywall("paywall")
                    showPaywall = false
                }
            },
            onDismiss = { showPaywall = false },
            onSecretUnlock = {
                viewModel.forcePro()
                showPaywall = false
            }
        )
    }
}
