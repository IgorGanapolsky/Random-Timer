import SwiftUI

enum PaywallEntryPoint: String {
    case rangeGate = "range_gate"
    case soundGate = "sound_gate"
    case unknown = "unknown"

    /// Maps to the analytics feature name for feature_gate_hit events.
    var featureGateName: String {
        switch self {
        case .rangeGate: return "extended_range"
        case .soundGate: return "pro_sounds"
        case .unknown: return "unknown"
        }
    }
}

struct PaywallSheet: View {
    static let hiddenUnlockHoldDuration: TimeInterval = 8.0
    static let headline = "Unlock Full Training Mode"
    static let subheadline = "Longer sessions, voice coaching, more sounds, and repeatable rounds."
    static let audienceLine = "Built for dry fire, sparring, drills, and reaction training."
    static let pricingFooter = "Pro Tactical — 1 Year — Auto-renews at $29.99/year. Cancel anytime."
    static let featureTitle = "PRO FEATURES"
    static let featureRows = [
        "Train up to 60-minute sessions",
        "Get voice callouts during training",
        "Use loop mode with round limits",
        "Unlock the full sound library",
        "New Pro voice callouts and sound packs every 30 days",
    ]

    // swiftlint:disable:next no_environment_object
    @EnvironmentObject var proManager: ProManager
    @Environment(\.dismiss) private var dismiss
    @State private var hasTrackedDismiss = false
    @State private var purchaseError: String?
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
                    Text(Self.headline)
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.textPrimary)

                    VStack(spacing: 4) {
                        Text(Self.subheadline)
                        Text(Self.audienceLine)
                        Text(Self.pricingFooter)
                    }
                    .font(.caption)
                    .foregroundColor(.textSecondary)
                    .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .contentShape(Rectangle())
                .highPriorityGesture(
                    LongPressGesture(minimumDuration: Self.hiddenUnlockHoldDuration, maximumDistance: 100)
                        .onEnded { _ in
                            triggerDebugUnlock()
                        }
                )

                VStack(alignment: .leading, spacing: 16) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(Self.featureTitle)
                            .font(.caption.bold())
                            .foregroundColor(.accentPrimary)
                        ForEach(Self.featureRows, id: \.self) { feature in
                            ProFeatureRow(text: feature)
                        }
                    }
                }
                .padding(.horizontal)

                VStack(spacing: 12) {
                    PrimaryButton(
                        title: "Start Pro \u{2022} \(normalizedPriceLabel(proManager.formattedPrice(for: ProManager.eliteProductID)))"
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

                // Required by App Store Guideline 3.1.2(c)
                HStack(spacing: 16) {
                    Link("Privacy Policy",
                         destination: URL(string: "https://igorganapolsky.github.io/Random-Timer/privacy-policy/")!)
                    Link("Terms of Use (EULA)",
                         destination: URL(string: "https://igorganapolsky.github.io/Random-Timer/eula/")!)
                }
                .font(.caption2)
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
        .alert("Purchase Issue", isPresented: Binding(
            get: { purchaseError != nil },
            set: { if !$0 { purchaseError = nil } }
        )) {
            Button("OK") { purchaseError = nil }
        } message: {
            Text(purchaseError ?? "")
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

        guard result == .success else {
            switch result {
            case .productUnavailable:
                purchaseError = "This product is currently unavailable. Please try again later."
            case .failed:
                purchaseError = "Purchase failed. Please check your connection and try again."
            case .pending:
                purchaseError = "Your purchase is pending approval."
            default:
                break
            }
            return
        }

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

    func normalizedPriceLabel(_ price: String) -> String {
        let trimmed = price.trimmingCharacters(in: .whitespacesAndNewlines)
        let lowered = trimmed.lowercased()
        if lowered.contains("/yr") || lowered.contains("/year") {
            return trimmed
        }
        return "\(trimmed)/year"
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
