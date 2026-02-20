package com.iganapolsky.randomtimer.ui.navigation

import android.app.Activity
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.iganapolsky.randomtimer.analytics.AnalyticsScreens
import com.iganapolsky.randomtimer.ui.screens.ActiveTimerScreen
import com.iganapolsky.randomtimer.ui.screens.TimerSetupScreen
import com.iganapolsky.randomtimer.ui.viewmodel.TimerViewModel

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
    val currentRoute = navController.currentBackStackEntryAsState().value?.destination?.route
    val activity = LocalContext.current as? Activity

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
                navController.popBackStack(Screen.Setup.route, inclusive = false)
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
            TimerSetupScreen(
                config = config,
                onConfigChange = viewModel::updateConfig,
                onStartTimer = viewModel::startTimer,
                onSoundPreview = viewModel::previewSound,
                onVolumePreview = viewModel::previewVolume,
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
            timerState?.let { state ->
                ActiveTimerScreen(
                    state = state,
                    onStop = {
                        viewModel.cancelTimer()
                        navController.popBackStack(Screen.Setup.route, inclusive = false)
                    },
                    onDismissAlarm = {
                        viewModel.dismissAlarm()
                        navController.popBackStack(Screen.Setup.route, inclusive = false)
                    },
                    onSilence = viewModel::silenceAlarm,
                    onPause = viewModel::pauseTimer,
                    onResume = viewModel::resumeTimer,
                    onReset = {
                        viewModel.resetTimer()
                    },
                    onLoopToggle = { enabled ->
                        viewModel.updateLoopSetting(enabled)
                    },
                )
            }
        }
    }
}
