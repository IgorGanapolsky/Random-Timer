import SwiftUI

private enum SubscriptionLegalLinks {
    static let termsOfUse = legalURL("https://www.apple.com/legal/internet-services/itunes/dev/stdeula/")
    static let privacyPolicy = legalURL("https://github.com/IgorGanapolsky/Random-Timer/blob/main/PRIVACY_POLICY.md")

    private static func legalURL(_ raw: String) -> URL {
        guard let url = URL(string: raw) else {
            preconditionFailure("Invalid legal URL: \(raw)")
        }
        return url
    }
}

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

            paywallTitle

            VStack(spacing: 4) {
                Text("One premium plan.")
                Text("Yearly auto-renewing subscription. Cancel anytime.")
            }
            .font(.caption)
            .foregroundColor(.textSecondary)
            .multilineTextAlignment(.center)

            VStack(alignment: .leading, spacing: 16) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("PRO FEATURES")
                        .font(.caption.bold())
                        .foregroundColor(.accentPrimary)
                    ProFeatureRow(text: "10 alarm sounds (vs 2 free)")
                    ProFeatureRow(text: "Extended range up to 60 minutes")
                    ProFeatureRow(text: "Spoken countdown cues + command callouts")
                    ProFeatureRow(text: "Support independent development")
                }
            }
            .padding(.horizontal)

            VStack(spacing: 12) {
                PrimaryButton(title: "Unlock Pro • \(proManager.formattedPrice(for: ProManager.eliteProductID))") {
                    Task {
                        await purchase(productID: ProManager.eliteProductID)
                    }
                }
            }

            VStack(spacing: 6) {
                Text("Subscription terms")
                    .font(.caption2.weight(.semibold))
                    .foregroundColor(.textSecondary)

                HStack(spacing: 16) {
                    Link("Terms of Use", destination: SubscriptionLegalLinks.termsOfUse)
                    Link("Privacy Policy", destination: SubscriptionLegalLinks.privacyPolicy)
                }
                .font(.caption2)
                .foregroundColor(.accentPrimary)
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

    @ViewBuilder
    private var paywallTitle: some View {
        let title =
            Text("Upgrade to Pro")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.textPrimary)
                .frame(maxWidth: .infinity)
                .contentShape(Rectangle())

#if DEBUG
        title.onLongPressGesture(minimumDuration: 8.0) {
            proManager.unlockProForDebug()
            hasTrackedDismiss = true
            dismiss()
        }
#else
        title
#endif
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
