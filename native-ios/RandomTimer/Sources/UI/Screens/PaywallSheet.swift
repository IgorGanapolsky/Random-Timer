import SwiftUI

enum PaywallEntryPoint: String {
    case rangeGate = "range_gate"
    case soundGate = "sound_gate"
    case unknown = "unknown"
}

struct PaywallSheet: View {
    // swiftlint:disable:next no_environment_object
    @EnvironmentObject var proManager: ProManager
    @Environment(\.dismiss) private var dismiss
    @State private var hasTrackedDismiss = false
    let entryPoint: PaywallEntryPoint

    var body: some View {
        ScrollView {
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

                VStack(spacing: 4) {
                    Text("Unlock Full Training Mode")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.textPrimary)

                    Text("Longer sessions, voice coaching, more sounds, and repeatable rounds.")
                        .font(.caption)
                        .foregroundColor(.textSecondary)
                        .multilineTextAlignment(.center)

                    Text("Built for dry fire, sparring, drills, and reaction training.")
                        .font(.caption)
                        .foregroundColor(.textMuted)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .contentShape(Rectangle())
                .highPriorityGesture(
                    LongPressGesture(minimumDuration: 8.0, maximumDistance: 100)
                        .onEnded { _ in
                            triggerDebugUnlock()
                        }
                )

                VStack(alignment: .leading, spacing: 8) {
                    ProFeatureRow(text: "Train up to 60-minute sessions")
                    ProFeatureRow(text: "Get voice callouts during training")
                    ProFeatureRow(text: "Use loop mode with round limits")
                    ProFeatureRow(text: "Unlock the full sound library")
                    ProFeatureRow(text: "New voice packs and sounds every 30 days")
                }
                .padding(.horizontal)

                VStack(spacing: 12) {
                    PrimaryButton(
                        title: "Start Pro \u{2022} \(proManager.formattedPrice(for: ProManager.eliteProductID))/year"
                    ) {
                        Task {
                            await purchase(productID: ProManager.eliteProductID)
                        }
                    }
                }

                Text("Cancel anytime. Auto-renews yearly.")
                    .font(.caption)
                    .foregroundColor(.textMuted)

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
            .padding(.top, 8)
            .padding(.bottom, 12)
            .frame(maxWidth: .infinity, alignment: .top)
        }
        .scrollIndicators(.hidden)
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

    @MainActor
    private func purchase(productID: String) async {
        AnalyticsService.shared.track(
            AnalyticsEvents.paywallPurchaseAttempt,
            properties: purchaseProperties(productID: productID)
        )

        let result = await proManager.purchase(productID: productID)

        // Compatibility event for existing dashboards while canonical events roll out.
        AnalyticsService.shared.track(
            AnalyticsEvents.paywallPurchaseResult,
            properties: purchaseProperties(productID: productID, result: result)
        )

        guard result == .success else { return }

        AnalyticsService.shared.track(
            AnalyticsEvents.paywallPurchaseSuccess,
            properties: purchaseProperties(productID: productID, result: result)
        )
        hasTrackedDismiss = true
        dismiss()
    }

    private func purchaseProperties(
        productID: String,
        result: ProPurchaseResult? = nil
    ) -> [String: Any] {
        var properties: [String: Any] = [
            AnalyticsProperties.entryPoint: entryPoint.rawValue,
            AnalyticsProperties.productId: productID,
        ]
        if let result {
            properties[AnalyticsProperties.result] = result.rawValue
        }
        return properties
    }

    private func trackDismiss(method: String) {
        guard !hasTrackedDismiss else { return }
        hasTrackedDismiss = true
        AnalyticsService.shared.track(AnalyticsEvents.paywallDismissed, properties: [
            AnalyticsProperties.entryPoint: entryPoint.rawValue,
            AnalyticsProperties.dismissMethod: method,
        ])
    }

    private func triggerDebugUnlock() {
        let generator = UIImpactFeedbackGenerator(style: .heavy)
        generator.impactOccurred()
        proManager.unlockProForDebug()
        hasTrackedDismiss = true
        dismiss()
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
