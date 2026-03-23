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
                    Text("Upgrade to Pro")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.textPrimary)

                    VStack(spacing: 4) {
                        Text("One premium plan.")
                        Text("Yearly auto-renewing subscription. Cancel anytime.")
                    }
                    .font(.caption)
                    .foregroundColor(.textSecondary)
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

                VStack(alignment: .leading, spacing: 16) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("PRO FEATURES")
                            .font(.caption.bold())
                            .foregroundColor(.accentPrimary)
                        ProFeatureRow(text: "10 alarm sounds (vs 2 free)")
                        ProFeatureRow(text: "Extended range up to 60 minutes")
                        ProFeatureRow(text: "Elapsed-time voice callouts")
                        ProFeatureRow(text: "Loop with optional round limits")
                        ProFeatureRow(text: "Monthly voice and sound refreshes")
                        ProFeatureRow(text: "Support independent development")
                    }
                }
                .padding(.horizontal)

                VStack(spacing: 12) {
                    PrimaryButton(
                        title: "Unlock Pro \u{2022} \(proManager.formattedPrice(for: ProManager.eliteProductID))"
                    ) {
                        Task {
                            await purchase(productID: ProManager.eliteProductID)
                        }
                    }
                }

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
