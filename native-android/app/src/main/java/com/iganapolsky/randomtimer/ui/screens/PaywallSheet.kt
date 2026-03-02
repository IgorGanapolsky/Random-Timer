package com.iganapolsky.randomtimer.ui.screens

import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.BuildConfig
import com.iganapolsky.randomtimer.ui.components.PrimaryButton
import com.iganapolsky.randomtimer.ui.theme.TimerColors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PaywallSheet(
    price: String,
    onPurchase: () -> Unit,
    onRestore: () -> Unit,
    onDismiss: () -> Unit,
    onDebugUnlock: (() -> Unit)? = null,
) {
    val debugUnlockEnabled = BuildConfig.DEBUG && onDebugUnlock != null
    val purchaseModifier =
        if (debugUnlockEnabled) {
            Modifier.combinedClickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null,
                onClick = onPurchase,
                onLongClick = { onDebugUnlock?.invoke() },
            )
        } else {
            Modifier
        }

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
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = TimerColors.TextPrimary,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "One-time purchase. No subscriptions.",
                style = MaterialTheme.typography.bodySmall,
                color = TimerColors.TextSecondary,
                textAlign = TextAlign.Center,
            )

            Spacer(modifier = Modifier.height(24.dp))

            ProFeatureRow(text = "10 alarm sounds (vs 2 free)")
            ProFeatureRow(text = "Extended range up to 60 minutes")
            ProFeatureRow(text = "Support independent development")

            Spacer(modifier = Modifier.height(32.dp))

            PrimaryButton(
                text = "Unlock Pro \u2022 $price",
                onClick = if (debugUnlockEnabled) ({}) else onPurchase,
                modifier = purchaseModifier,
            )

            Spacer(modifier = Modifier.height(8.dp))

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
