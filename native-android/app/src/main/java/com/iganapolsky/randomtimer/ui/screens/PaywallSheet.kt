package com.iganapolsky.randomtimer.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.waitForUpOrCancellation
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.ui.components.PrimaryButton
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import kotlinx.coroutines.withTimeoutOrNull

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PaywallSheet(
    basePrice: String,
    elitePrice: String = "",
    onPurchase: (String) -> Unit,
    onRestore: () -> Unit,
    onDismiss: () -> Unit,
    onDebugUnlock: (() -> Unit)? = null,
) {
    val haptic = LocalHapticFeedback.current
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = TimerColors.BackgroundDark,
    ) {
        Column(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = "Upgrade to Pro",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = TimerColors.TextPrimary,
                textAlign = TextAlign.Center,
                modifier =
                    Modifier.fillMaxWidth().then(
                        if (onDebugUnlock != null) {
                            Modifier.holdForHiddenUnlock(
                                holdDurationMs = 8_000L,
                                haptic = haptic,
                                onHoldComplete = onDebugUnlock,
                            )
                        } else {
                            Modifier
                        },
                    ),
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "One-time purchase. Yours forever.",
                style = MaterialTheme.typography.bodySmall,
                color = TimerColors.TextSecondary,
            )

            Spacer(modifier = Modifier.height(24.dp))

            ProFeatureRow(text = "10 alarm sounds (vs 2 free)")
            ProFeatureRow(text = "Extended range up to 60 minutes")
            ProFeatureRow(text = "Timer presets library")
            ProFeatureRow(text = "Full workout history")
            ProFeatureRow(text = "All future updates included")

            Spacer(modifier = Modifier.height(24.dp))

            PrimaryButton(
                text = "Unlock Pro \u2022 $basePrice",
                onClick = { onPurchase("pro_base") },
            )

            if (elitePrice.isNotEmpty()) {
                Spacer(modifier = Modifier.height(20.dp))

                HorizontalDivider(color = TimerColors.TextSecondary.copy(alpha = 0.3f))

                Spacer(modifier = Modifier.height(20.dp))

                Text(
                    text = "Elite Tactical",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = TimerColors.TextPrimary,
                    textAlign = TextAlign.Center,
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = "Monthly subscription",
                    style = MaterialTheme.typography.bodySmall,
                    color = TimerColors.TextSecondary,
                )

                Spacer(modifier = Modifier.height(16.dp))

                ProFeatureRow(text = "Unlimited custom sounds (upload your own)")
                ProFeatureRow(text = "Up to 4 hours timer duration")
                ProFeatureRow(text = "Unlimited presets + cloud sync")
                ProFeatureRow(text = "Priority feature requests")

                Spacer(modifier = Modifier.height(16.dp))

                PrimaryButton(
                    text = "Unlock Elite \u2022 $elitePrice/mo",
                    onClick = { onPurchase("elite_tactical") },
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "Restore purchase",
                style = MaterialTheme.typography.labelMedium,
                color = TimerColors.TextSecondary,
                modifier =
                    Modifier
                        .padding(bottom = 16.dp)
                        .clickable(onClick = onRestore),
                textAlign = TextAlign.Center,
            )

            Text(
                text = "Not now",
                style = MaterialTheme.typography.labelMedium,
                color = TimerColors.TextSecondary,
                modifier =
                    Modifier
                        .padding(bottom = 16.dp)
                        .clickable(onClick = onDismiss),
                textAlign = TextAlign.Center,
            )
        }
    }
}

private fun Modifier.holdForHiddenUnlock(
    holdDurationMs: Long,
    haptic: androidx.compose.ui.hapticfeedback.HapticFeedback,
    onHoldComplete: () -> Unit,
): Modifier =
    pointerInput(holdDurationMs, onHoldComplete) {
        awaitPointerEventScope {
            while (true) {
                val down = awaitFirstDown(requireUnconsumed = false)
                val startTime = System.currentTimeMillis()
                var isReleased = false
                
                // Track the touch until it's released or the duration passes
                while (!isReleased) {
                    val event = awaitPointerEvent()
                    val currentTime = System.currentTimeMillis()
                    
                    if (event.changes.any { it.changedToUp() }) {
                        isReleased = true
                    } else if (currentTime - startTime >= holdDurationMs) {
                        // Success!
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        onHoldComplete()
                        // Wait for release before allowing another hold
                        while (!isReleased) {
                            val releaseEvent = awaitPointerEvent()
                            if (releaseEvent.changes.any { it.changedToUp() }) {
                                isReleased = true
                            }
                        }
                        return@awaitPointerEventScope
                    }
                }
            }
        }
    }

@Composable
private fun ProFeatureRow(text: String) {
    Row(
        modifier =
            Modifier
                .fillMaxWidth()
                .padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.Start,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = "\u2713",
            style = MaterialTheme.typography.bodyMedium,
            color = TimerColors.AccentPrimary,
            modifier = Modifier.padding(end = 12.dp),
        )
        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            color = TimerColors.TextPrimary,
        )
    }
}
