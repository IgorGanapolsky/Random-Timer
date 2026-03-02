package com.iganapolsky.randomtimer.ui.screens

import androidx.compose.foundation.clickable
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.ui.components.PrimaryButton
import com.iganapolsky.randomtimer.ui.theme.TimerColors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PaywallSheet(
    basePrice: String,
    elitePrice: String,
    onPurchase: (String) -> Unit,
    onRestore: () -> Unit,
    onDismiss: () -> Unit,
) {
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = TimerColors.BackgroundDark,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = "Hybrid Tactical Monetization",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = TimerColors.TextPrimary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Tactical Base
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 8.dp)
            ) {
                Text(
                    text = "Tactical Base",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = TimerColors.AccentPrimary
                )
                Text(
                    text = "One-time purchase. Essential tactical features.",
                    style = MaterialTheme.typography.bodySmall,
                    color = TimerColors.TextSecondary
                )
                Spacer(modifier = Modifier.height(8.dp))
                ProFeatureRow(text = "10 alarm sounds (vs 2 free)")
                ProFeatureRow(text = "Extended range up to 60 minutes")
                Spacer(modifier = Modifier.height(8.dp))
                PrimaryButton(
                    text = "Unlock Base \u2022 $basePrice",
                    onClick = { onPurchase("pro_base") }
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Tactical Elite
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 8.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "Tactical Elite",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = TimerColors.AccentPrimary
                    )
                    Spacer(modifier = Modifier.weight(1f))
                    Text(
                        text = "RECOMMENDED",
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = TimerColors.TextPrimary,
                        modifier = Modifier.padding(horizontal = 4.dp)
                    )
                }
                Text(
                    text = "Subscription. The ultimate tactical experience.",
                    style = MaterialTheme.typography.bodySmall,
                    color = TimerColors.TextSecondary
                )
                Spacer(modifier = Modifier.height(8.dp))
                ProFeatureRow(text = "Includes all Base features")
                ProFeatureRow(text = "AI Voice Callouts (Coming Soon)")
                ProFeatureRow(text = "Support independent development")
                Spacer(modifier = Modifier.height(8.dp))
                PrimaryButton(
                    text = "Unlock Elite \u2022 $elitePrice",
                    onClick = { onPurchase("elite_tactical") }
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "Restore purchase",
                style = MaterialTheme.typography.labelMedium,
                color = TimerColors.TextSecondary,
                modifier = Modifier
                    .padding(bottom = 16.dp)
                    .clickable(onClick = onRestore),
                textAlign = TextAlign.Center,
            )

            Text(
                text = "Not now",
                style = MaterialTheme.typography.labelMedium,
                color = TimerColors.TextSecondary,
                modifier = Modifier
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
