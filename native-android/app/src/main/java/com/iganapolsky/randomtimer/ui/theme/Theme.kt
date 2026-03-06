package com.iganapolsky.randomtimer.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext

private val DarkColorScheme =
    darkColorScheme(
        primary = TimerColors.AccentPrimary,
        secondary = TimerColors.AccentSecondary,
        tertiary = TimerColors.AccentSecondary,
        background = TimerColors.BackgroundDark,
        surface = TimerColors.BackgroundLight,
        onPrimary = TimerColors.TextPrimary,
        onSecondary = TimerColors.TextPrimary,
        onTertiary = TimerColors.TextPrimary,
        onBackground = TimerColors.TextPrimary,
        onSurface = TimerColors.TextPrimary,
        surfaceVariant = TimerColors.GlassBackground,
        onSurfaceVariant = TimerColors.TextSecondary,
    )

@Composable
fun RandomTimerTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    // Dynamic color is available on Android 12+
    dynamicColor: Boolean = false, // Disabled by default for consistent branding
    content: @Composable () -> Unit,
) {
    val colorScheme =
        when {
            dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
                val context = LocalContext.current
                if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
            }
            // Always use dark theme for timer app
            else -> DarkColorScheme
        }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content,
    )
}
