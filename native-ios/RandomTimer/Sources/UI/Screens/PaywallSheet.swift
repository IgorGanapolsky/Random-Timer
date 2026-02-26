import SwiftUI

enum PaywallEntryPoint: String {
    case rangeGate = "range_gate"
    case soundGate = "sound_gate"
    case unknown = "unknown"
}

struct PaywallSheet: View {
    @EnvironmentObject var proManager: ProManager
    @Environment(\.dismiss) private var dismiss
    @State private var hasTrackedDismiss = false
    let entryPoint: PaywallEntryPoint

    var body: some View {
        VStack(spacing: 24) {
            HStack {
                Spacer()
                Button {
                    trackDismiss(method: "close_button")
                    dismiss()
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title3)
                        .foregroundColor(.textSecondary)
                        .accessibilityLabel("Close paywall")
                }
            }

            Text("Upgrade to Pro")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.textPrimary)

            Text("One-time purchase. No subscriptions.")
                .font(.caption)
                .foregroundColor(.textSecondary)

            VStack(alignment: .leading, spacing: 12) {
                ProFeatureRow(text: "10 alarm sounds (vs 2 free)")
                ProFeatureRow(text: "Extended range up to 60 minutes")
                ProFeatureRow(text: "Support independent development")
            }
            .padding(.horizontal)

            PrimaryButton(title: "Unlock Pro \u{2022} \(proManager.formattedPrice)") {
                Task {
                    let result = await proManager.purchase()
                    AnalyticsService.shared.track(AnalyticsEvents.paywallPurchaseResult, properties: [
                        AnalyticsProperties.entryPoint: entryPoint.rawValue,
                        AnalyticsProperties.result: result.rawValue,
                    ])

                    if result == .success {
                        hasTrackedDismiss = true
                        dismiss()
                    }
                }
            }
#if DEBUG
            .onLongPressGesture(minimumDuration: 0.8) {
                proManager.unlockProForDebug()
                hasTrackedDismiss = true
                AnalyticsService.shared.track(AnalyticsEvents.paywallPurchaseResult, properties: [
                    AnalyticsProperties.entryPoint: entryPoint.rawValue,
                    AnalyticsProperties.result: "dev_override",
                ])
                dismiss()
            }
#endif

            Button("Restore purchase") {
                Task {
                    let result = await proManager.restorePurchases()
                    AnalyticsService.shared.track(AnalyticsEvents.paywallRestoreResult, properties: [
                        AnalyticsProperties.entryPoint: entryPoint.rawValue,
                        AnalyticsProperties.result: result.rawValue,
                    ])

                    if result == .restored || result == .alreadyUnlocked {
                        hasTrackedDismiss = true
                        dismiss()
                    }
                }
            }
            .font(.footnote)
            .foregroundColor(.textSecondary)

            Button("Not now") {
                trackDismiss(method: "not_now")
                dismiss()
            }
            .font(.footnote)
            .foregroundColor(.textSecondary)
        }
        .padding(24)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(Color.backgroundDark)
        .task {
            AnalyticsService.shared.track(AnalyticsEvents.paywallViewed, properties: [
                AnalyticsProperties.entryPoint: entryPoint.rawValue,
            ])
            await proManager.fetchProduct()
        }
        .onDisappear {
            trackDismiss(method: "system")
        }
    }

    private func trackDismiss(method: String) {
        guard !hasTrackedDismiss else { return }
        hasTrackedDismiss = true
        AnalyticsService.shared.track(AnalyticsEvents.paywallDismissed, properties: [
            AnalyticsProperties.entryPoint: entryPoint.rawValue,
            AnalyticsProperties.dismissMethod: method,
        ])
    }
}

private struct ProFeatureRow: View {
    let text: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "checkmark")
                .foregroundColor(.accentPrimary)
                .font(.body)
            Text(text)
                .font(.body)
                .foregroundColor(.textPrimary)
        }
    }
}
