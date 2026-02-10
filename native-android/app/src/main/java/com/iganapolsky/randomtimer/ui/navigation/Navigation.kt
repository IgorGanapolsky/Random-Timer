package com.iganapolsky.randomtimer.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.iganapolsky.randomtimer.ui.screens.ActiveTimerScreen
import com.iganapolsky.randomtimer.ui.screens.TimerSetupScreen
import com.iganapolsky.randomtimer.ui.viewmodel.TimerViewModel

sealed class Screen(val route: String) {
    data object Setup : Screen("setup")
    data object ActiveTimer : Screen("active_timer")
}

@Composable
fun RandomTimerNavHost(
    navController: NavHostController = rememberNavController(),
    viewModel: TimerViewModel = hiltViewModel()
) {
    val config by viewModel.config.collectAsState()
    val timerState by viewModel.timerState.collectAsState()

    // Auto-navigate based on timer state
    LaunchedEffect(timerState) {
        val currentRoute = navController.currentDestination?.route
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
            }
        }
    }

    NavHost(
        navController = navController,
        startDestination = Screen.Setup.route
    ) {
        composable(Screen.Setup.route) {
            TimerSetupScreen(
                config = config,
                onConfigChange = viewModel::updateConfig,
                onStartTimer = {
                    viewModel.startTimer()
                    navController.navigate(Screen.ActiveTimer.route) {
                        launchSingleTop = true
                    }
                },
                onSoundPreview = viewModel::previewSound,
                onVolumePreview = viewModel::previewVolume
            )
        }

        composable(Screen.ActiveTimer.route) {
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
                    onPause = viewModel::pauseTimer,
                    onResume = viewModel::resumeTimer,
                    onReset = {
                        viewModel.resetTimer()
                    },
                    onLoopToggle = { enabled ->
                        viewModel.updateLoopSetting(enabled)
                    }
                )
            }
        }
    }
}
