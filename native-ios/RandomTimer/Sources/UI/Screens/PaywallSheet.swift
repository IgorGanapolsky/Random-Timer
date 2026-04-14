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

/// Which plan option is highlighted on the paywall.
enum PaywallPlanSelection {
    case monthly
    case annual
    case lifetime
}

struct PaywallSheet: View {
    static let hiddenUnlockHoldDuration: TimeInterval = 8.0
    static let headline = "Stop Training With the Brakes On"
    static let subheadline =
        "Go unlimited — sessions up to 60 minutes, live voice callouts, "
        + "and a full sound library that updates every month."
    static let subscriptionFooter =
        "Cancel anytime. Subscription auto-renews until cancelled. "
        + "Price shown on Apple's confirmation sheet."
    static let featureTitle = "PRO FEATURES"
    static let featureRows = [
        "Full-length sessions — up to 60 minutes, no cutoffs",
        "Live voice callouts keep you sharp under pressure",
        "Loop drills with round limits — just like competition",
        "Full sound arsenal — real bells, horns, and sirens",
        "Fresh callout packs every 30 days — Pro gets them first",
    ]

    @EnvironmentObject var proManager: ProManager
    @Environment(\.dismiss) private var dismiss
    @State private var hasTrackedDismiss = false
    @State private var purchaseError: String?
    /// Default to monthly — lowest barrier to entry.
    @State private var selectedPlan: PaywallPlanSelection = .monthly
    @State private var introOfferEligibleProductIDs: Set<String> = []
    let entryPoint: PaywallEntryPoint

    // MARK: - Derived helpers

    private var monthlyPrice: String {
        proManager.formattedPrice(for: ProManager.monthlyProductID)
    }

    private var annualPrice: String {
        proManager.formattedPrice(for: ProManager.annualProductID)
    }

    private var lifetimePrice: String {
        proManager.formattedPrice(for: ProManager.paywallProductID)
    }

    private var selectedProductID: String {
        switch selectedPlan {
        case .monthly: return ProManager.monthlyProductID
        case .annual: return ProManager.annualProductID
        case .lifetime: return ProManager.paywallProductID
        }
    }

    private var productsEligibilityKey: String {
        proManager.products.map(\.id).sorted().joined(separator: "|")
    }

    private var ctaLabel: String {
        if introOfferEligibleProductIDs.contains(selectedProductID) {
            return "Start 7-Day Free Trial"
        }
        switch selectedPlan {
        case .monthly: return "Start Monthly \u{2022} \(monthlyPrice)/mo"
        case .annual: return "Start Annual \u{2022} \(annualPrice)/yr"
        case .lifetime: return "Unlock Lifetime \u{2022} \(lifetimePrice)"
        }
    }

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
                        Text(Self.subscriptionFooter)
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

                // Plan selector
                VStack(alignment: .leading, spacing: 8) {
                    Text("CHOOSE A PLAN")
                        .font(.caption.bold())
                        .foregroundColor(.accentPrimary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal)

                    PlanOptionRow(
                        title: "Monthly",
                        priceLabel: "\(monthlyPrice)/month",
                        badge: nil,
                        isSelected: selectedPlan == .monthly
                    ) {
                        selectedPlan = .monthly
                        trackOfferSelected(plan: "monthly", productID: ProManager.monthlyProductID)
                    }

                    PlanOptionRow(
                        title: "Annual",
                        priceLabel: "\(annualPrice)/year",
                        badge: "Best Value",
                        isSelected: selectedPlan == .annual
                    ) {
                        selectedPlan = .annual
                        trackOfferSelected(plan: "annual", productID: ProManager.annualProductID)
                    }

                    PlanOptionRow(
                        title: "Lifetime",
                        priceLabel: lifetimePrice,
                        badge: "One-time",
                        isSelected: selectedPlan == .lifetime
                    ) {
                        selectedPlan = .lifetime
                        trackOfferSelected(plan: "lifetime", productID: ProManager.paywallProductID)
                    }
                }

                VStack(spacing: 12) {
                    PrimaryButton(title: ctaLabel) {
                        Task {
                            await purchase(productID: selectedProductID)
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
                // swiftlint:disable force_unwrapping
                HStack(spacing: 16) {
                    Link(
                        "Privacy Policy",
                        destination: URL(string: "https://igorganapolsky.github.io/Random-Timer/privacy-policy/")!
                    )
                    Link(
                        "Terms of Use (EULA)",
                        destination: URL(string: "https://igorganapolsky.github.io/Random-Timer/eula/")!
                    )
                }
                // swiftlint:enable force_unwrapping
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
            AnalyticsService.shared.track(AnalyticsEvents.paywallView, properties: [
                AnalyticsProperties.entryPoint: entryPoint.rawValue,
            ])
            AnalyticsService.shared.track(AnalyticsEvents.paywallViewed, properties: [
                AnalyticsProperties.entryPoint: entryPoint.rawValue,
            ])
            await proManager.fetchProduct()
            await refreshIntroOfferEligibility()
        }
        .task(id: productsEligibilityKey) {
            await refreshIntroOfferEligibility()
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
            // Track purchase_failed with categorized reason
            let failReason: String
            switch result {
            case .userCancelled:
                failReason = "user_cancelled"
            case .productUnavailable:
                failReason = "product_unavailable"
            case .failed:
                failReason = "network"
            case .pending:
                failReason = "pending"
            default:
                failReason = "unknown"
            }
            AnalyticsService.shared.track(AnalyticsEvents.purchaseFailed, properties: [
                AnalyticsProperties.reason: failReason,
                AnalyticsProperties.productId: productID,
                AnalyticsProperties.entryPoint: entryPoint.rawValue,
            ])
            if result != .userCancelled {
                AnalyticsService.shared.track(AnalyticsEvents.paywallPurchaseFailReason, properties: [
                    AnalyticsProperties.reason: failReason,
                    AnalyticsProperties.productId: productID,
                    AnalyticsProperties.entryPoint: entryPoint.rawValue,
                ])
            }

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
            properties: purchaseProperties(productID: productID, result: result, includeRevenue: true)
        )
        hasTrackedDismiss = true
        dismiss()
    }

    @MainActor
    private func refreshIntroOfferEligibility() async {
        var eligibleProductIDs: Set<String> = []
        for productID in [ProManager.monthlyProductID, ProManager.annualProductID] {
            guard let product = proManager.products.first(where: { $0.id == productID }),
                  let subscription = product.subscription
            else { continue }
            if await subscription.isEligibleForIntroOffer {
                eligibleProductIDs.insert(productID)
            }
        }
        introOfferEligibleProductIDs = eligibleProductIDs
    }

    private func purchaseProperties(
        productID: String,
        result: ProPurchaseResult? = nil,
        includeRevenue: Bool = false
    ) -> [String: Any] {
        var properties: [String: Any] = [
            AnalyticsProperties.entryPoint: entryPoint.rawValue,
            AnalyticsProperties.productId: productID,
        ]
        if let result {
            properties[AnalyticsProperties.result] = result.rawValue
        }
        // Include numeric price so PostHog can compute actual revenue.
        if includeRevenue,
           let product = proManager.products.first(where: { $0.id == productID }) {
            properties[AnalyticsProperties.revenue] = NSDecimalNumber(decimal: product.price).doubleValue
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

    private func trackOfferSelected(plan: String, productID: String) {
        AnalyticsService.shared.track(AnalyticsEvents.paywallOfferSelect, properties: [
            AnalyticsProperties.entryPoint: entryPoint.rawValue,
            AnalyticsProperties.productId: productID,
            "plan": plan,
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

private struct PlanOptionRow: View {
    let title: String
    let priceLabel: String
    let badge: String?
    let isSelected: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.body.weight(.semibold))
                        .foregroundColor(.textPrimary)
                    Text(priceLabel)
                        .font(.caption)
                        .foregroundColor(.textSecondary)
                }
                Spacer()
                if let badge {
                    Text(badge)
                        .font(.caption.bold())
                        .foregroundColor(.accentPrimary)
                        .padding(.trailing, 4)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isSelected ? Color.accentPrimary.opacity(0.08) : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? Color.accentPrimary : Color.textSecondary.opacity(0.3),
                            lineWidth: isSelected ? 2 : 1)
            )
            .padding(.horizontal)
        }
        .buttonStyle(.plain)
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
