package com.iganapolsky.randomtimer.ui.theme

import androidx.compose.ui.graphics.Color

// Legacy Material defaults (unused - kept for reference)
val Purple80 = Color(0xFFD0BCFF)
val PurpleGrey80 = Color(0xFFCCC2DC)
val Pink80 = Color(0xFFEFB8C8)

val Purple40 = Color(0xFF6650a4)
val PurpleGrey40 = Color(0xFF625b71)
val Pink40 = Color(0xFF7D5260)

// Timer state colors - Tactical crimson palette
object TimerColors {
    // Background gradient - pure black, no purple tint
    val BackgroundDark = Color(0xFF0A0A0F)
    val BackgroundLight = Color(0xFF141419)

    // Timer ring states
    val TimerActive = Color(0xFF10B981) // Emerald green - running
    val TimerWarning = Color(0xFFF59E0B) // Amber - < 30 seconds
    val TimerDanger = Color(0xFFEF4444) // Rose red - < 10 seconds
    val TimerComplete = Color(0xFFDC2626) // Crimson red - complete/alarm

    // Glassmorphism
    val GlassBackground = Color(0x1AFFFFFF) // 10% white
    val GlassBorder = Color(0x33FFFFFF) // 20% white
    val GlassHighlight = Color(0x4DFFFFFF) // 30% white

    // Text
    val TextPrimary = Color(0xFFF8FAFC) // Near white
    val TextSecondary = Color(0xFFA1A1AA) // Muted gray
    val TextMuted = Color(0xFF71717A) // Dim gray

    // Accent
    val AccentPrimary = Color(0xFFDC2626) // Crimson red
    val AccentSecondary = Color(0xFFEF4444) // Bright red

    // Slider
    val SliderTrack = Color(0xFF3F3F46)
    val SliderThumb = Color(0xFFF8FAFC)
}
