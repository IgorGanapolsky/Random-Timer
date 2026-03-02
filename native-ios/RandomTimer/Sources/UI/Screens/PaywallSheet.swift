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
                Button("Not now") {
                    trackDismiss(method: "header_not_now")
                    dismiss()
                }
                .font(.footnote.weight(.semibold))
                .foregroundColor(.textSecondary)

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

            VStack(alignment: .leading, spacing: 16) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("PRO FEATURES")
                        .font(.caption.bold())
                        .foregroundColor(.accentPrimary)
                    ProFeatureRow(text: "10 alarm sounds (vs 2 free)")
                    ProFeatureRow(text: "Extended range up to 60 minutes")
                }

                Divider().background(Color.glassBorder)

                VStack(alignment: .leading, spacing: 8) {
                    Text("ELITE FEATURES")
                        .font(.caption.bold())
                        .foregroundColor(.accentPrimary)
                    ProFeatureRow(text: "AI Voice Callouts (Real-time coaching)")
                    ProFeatureRow(text: "Unlocks everything forever")
                }
            }
            .padding(.horizontal)

            VStack(spacing: 12) {
                PrimaryButton(title: "Unlock Pro \u{2022} \(proManager.formattedPrice(for: ProManager.baseProductID))") {
                    Task {
                        let result = await proManager.purchase(productID: ProManager.baseProductID)
                        AnalyticsService.shared.track(AnalyticsEvents.paywallPurchaseResult, properties: [
                            AnalyticsProperties.entryPoint: entryPoint.rawValue,
                            AnalyticsProperties.result: result.rawValue,
                            "product_id": ProManager.baseProductID
                        ])

                        if result == .success {
                            hasTrackedDismiss = true
                            dismiss()
                        }
                    }
                }

                PrimaryButton(title: "Go Elite \u{2022} \(proManager.formattedPrice(for: ProManager.eliteProductID))") {
                    Task {
                        let result = await proManager.purchase(productID: ProManager.eliteProductID)
                        AnalyticsService.shared.track(AnalyticsEvents.paywallPurchaseResult, properties: [
                            AnalyticsProperties.entryPoint: entryPoint.rawValue,
                            AnalyticsProperties.result: result.rawValue,
                            "product_id": ProManager.eliteProductID
                        ])

                        if result == .success {
                            hasTrackedDismiss = true
                            dismiss()
                        }
                    }
                }
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.accentPrimary, lineWidth: 2)
                )
            }
            #if DEBUG
            .onLongPressGesture(minimumDuration: 8.0) {
                proManager.unlockEliteForDebug()
                hasTrackedDismiss = true
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
                trackDismiss(method: "footer_not_now")
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
