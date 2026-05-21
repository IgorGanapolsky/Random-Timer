import SwiftUI

enum PaywallEntryPoint: String {
    case setupUpgradeCTA = "setup_upgrade_cta"
    case rangeGate = "range_gate"
    case voiceGate = "voice_gate"
    case repeatGate = "repeat_gate"
    case soundArsenalGate = "sound_arsenal_gate"
    case qualifiedTrainingGate = "qualified_training_gate"
    case unknown = "unknown"

    /// Maps to the analytics feature name for feature_gate_hit events.
    var featureGateName: String {
        switch self {
        case .setupUpgradeCTA: return "setup_upgrade_cta"
        case .rangeGate: return "extended_range"
        case .voiceGate: return "voice_callouts"
        case .repeatGate: return "repeat_loop"
        case .soundArsenalGate: return "pro_sounds"
        case .qualifiedTrainingGate: return "qualified_training_gate"
        case .unknown: return "unknown"
        }
    }
}

struct PaywallFeatureContext: Equatable {
    let eyebrow: String
    let valueCopy: String
}

func paywallFeatureContext(for entryPoint: PaywallEntryPoint) -> PaywallFeatureContext {
    switch entryPoint {
    case .setupUpgradeCTA:
        return PaywallFeatureContext(
            eyebrow: "You tapped Unlock Pro",
            valueCopy: "Pro turns the setup screen into a full training console: longer random windows, "
                + "live callouts, round caps, and the full sound arsenal."
        )
    case .rangeGate:
        return PaywallFeatureContext(
            eyebrow: "You tapped 60-minute random windows",
            valueCopy: "Pro removes the 5-minute cap so long rounds, circuits, "
                + "and stress drills can run on your timing."
        )
    case .voiceGate:
        return PaywallFeatureContext(
            eyebrow: "You tapped voice callouts",
            valueCopy: "Pro adds time checks plus combat, MMA, and conditioning cues "
                + "without revealing the random timer."
        )
    case .repeatGate:
        return PaywallFeatureContext(
            eyebrow: "You tapped round control",
            valueCopy: "Pro lets you cap loops from 1-100 rounds instead of guessing when a training block should end."
        )
    case .soundArsenalGate:
        return PaywallFeatureContext(
            eyebrow: "You tapped the sound arsenal",
            valueCopy: "Pro lets you equip the full alarm arsenal instead of only previewing locked sounds."
        )
    case .qualifiedTrainingGate:
        return PaywallFeatureContext(
            eyebrow: "Three sessions logged",
            valueCopy: "You are training like a serious athlete. Pro unlocks longer random windows, combat callouts, "
                + "round caps, and the full sound arsenal for your next block."
        )
    case .unknown:
        return PaywallFeatureContext(
            eyebrow: "Pro Tactical",
            valueCopy: "Unlock longer random windows, combat callouts, round caps, and the full sound arsenal."
        )
    }
}

/// Which plan option is highlighted on the paywall.
enum PaywallPlanSelection {
    case monthly
    case annual
    case lifetime
}

func initialPaywallPlanSelection(
    entryPoint: PaywallEntryPoint,
    defaultToAnnualExperiment: Bool
) -> PaywallPlanSelection {
    if defaultToAnnualExperiment {
        return .annual
    }
    if entryPoint == .setupUpgradeCTA {
        return .lifetime
    }
    return .monthly
}

func shouldShowPaywallPlan(
    _ plan: PaywallPlanSelection,
    availableProductIDs: Set<String>
) -> Bool {
    if availableProductIDs.isEmpty {
        return plan != .monthly
    }

    let requiredProductID: String
    switch plan {
    case .monthly:
        requiredProductID = ProManager.monthlyProductID
    case .annual:
        requiredProductID = ProManager.annualProductID
    case .lifetime:
        requiredProductID = ProManager.paywallProductID
    }
    return availableProductIDs.contains(requiredProductID)
}

/// True when StoreKit returned the product for this plan (required before launching purchase).
func hasPurchasablePaywallPlan(
    _ plan: PaywallPlanSelection,
    availableProductIDs: Set<String>
) -> Bool {
    !availableProductIDs.isEmpty && shouldShowPaywallPlan(plan, availableProductIDs: availableProductIDs)
}

func hasAnyPurchasablePaywallPlan(availableProductIDs: Set<String>) -> Bool {
    [PaywallPlanSelection.monthly, .annual, .lifetime].contains {
        hasPurchasablePaywallPlan($0, availableProductIDs: availableProductIDs)
    }
}

struct PaywallSheet: View {
    static let hiddenUnlockHoldDuration: TimeInterval = 8.0
    static let headline = "Unlock Full Fight-Ready Training"
    static let headlineOutcomesFirst = "Finish Strong With Full Random Pressure"
    static let subheadline =
        "Unlock 60-minute random windows, combat voice callouts, round-capped loops, "
        + "and the full sound arsenal built for pressure drills."
    static let subheadlineOutcomesFirst =
        "Longer random windows, combat callouts, and full-spectrum sounds — "
        + "built so every rep feels closer to live pressure."
    static let subscriptionFooter =
        "Elite plans from about $4.99–9.99/mo (store price on checkout). Cancel anytime; "
        + "subscription auto-renews until cancelled."
    static let featureTitle = "PRO FEATURES"
    static let featureRows = [
        "Ad-free training — Elite subscription removes rewarded ads",
        "60-minute random windows for full-length drills",
        "Combat and MMA voice callouts with live time checks",
        "Round-capped loops for pad work, sparring, and circuits",
        "Full sound arsenal — bells, horns, sirens, and more",
        "Fresh pro audio drops when new packs land",
    ]

    @EnvironmentObject var proManager: ProManager
    @Environment(\.dismiss) private var dismiss
    @State private var hasTrackedDismiss = false
    @State private var purchaseError: String?
    @State private var selectedPlan: PaywallPlanSelection
    @State private var introOfferEligibleProductIDs: Set<String> = []
    let entryPoint: PaywallEntryPoint
    let defaultToAnnualExperiment: Bool
    let valueFramingVariant: String

    init(
        entryPoint: PaywallEntryPoint,
        defaultToAnnualExperiment: Bool = false,
        valueFramingVariant: String = PaywallValueFraming.control
    ) {
        self.entryPoint = entryPoint
        self.defaultToAnnualExperiment = defaultToAnnualExperiment
        self.valueFramingVariant = valueFramingVariant
        _selectedPlan = State(initialValue: initialPaywallPlanSelection(
            entryPoint: entryPoint,
            defaultToAnnualExperiment: defaultToAnnualExperiment
        ))
    }

    private var displayHeadline: String {
        valueFramingVariant == PaywallValueFraming.outcomesFirst
            ? Self.headlineOutcomesFirst
            : Self.headline
    }

    private var displaySubheadline: String {
        valueFramingVariant == PaywallValueFraming.outcomesFirst
            ? Self.subheadlineOutcomesFirst
            : Self.subheadline
    }

    private var featureContext: PaywallFeatureContext {
        paywallFeatureContext(for: entryPoint)
    }

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

    private var availableProductIDs: Set<String> {
        Set(proManager.products.map(\.id))
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

    /// Never pass an all-whitespace title to `PrimaryButton` (empty labels can disappear in sheets).
    private var canPurchaseSelectedPlan: Bool {
        hasPurchasablePaywallPlan(selectedPlan, availableProductIDs: availableProductIDs)
    }

    private var ctaButtonTitle: String {
        if availableProductIDs.isEmpty {
            return "Loading plans…"
        }
        if !canPurchaseSelectedPlan {
            return "Purchases unavailable"
        }
        let trimmed = ctaLabel.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? "Continue" : trimmed
    }

    /// Headline, value props, and plan picker — scrolls so the purchase strip can stay pinned.
    @ViewBuilder
    private var paywallScrollContent: some View {
        VStack(spacing: 24) {
            HStack {
                Button("Not now") {
                    trackDismiss(method: "header_not_now")
                    dismiss()
                }
                .font(.footnote.weight(.semibold))
                .foregroundColor(.textSecondary)

                Spacer()

                Button("Restore purchase") {
                    Task {
                        await restorePurchaseFromPaywall()
                    }
                }
                .font(.footnote.weight(.semibold))
                .foregroundColor(.textSecondary)

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
                Text(displayHeadline)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.textPrimary)

                VStack(spacing: 4) {
                    Text(displaySubheadline)
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

            VStack(alignment: .leading, spacing: 4) {
                Text(featureContext.eyebrow)
                    .font(.caption.bold())
                    .foregroundColor(.accentPrimary)
                Text(featureContext.valueCopy)
                    .font(.caption)
                    .foregroundColor(.textPrimary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(14)
            .background(
                RoundedRectangle(cornerRadius: 14)
                    .fill(Color.accentPrimary.opacity(0.08))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(Color.accentPrimary.opacity(0.25), lineWidth: 1)
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

            VStack(alignment: .leading, spacing: 8) {
                Text("CHOOSE A PLAN")
                    .font(.caption.bold())
                    .foregroundColor(.accentPrimary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)

                if shouldShowPaywallPlan(.lifetime, availableProductIDs: availableProductIDs) {
                    PlanOptionRow(
                        title: "Lifetime",
                        priceLabel: lifetimePrice,
                        badge: "One-time",
                        isSelected: selectedPlan == .lifetime
                    ) {
                        selectedPlan = .lifetime
                        trackOfferSelected(
                            plan: "lifetime",
                            productID: ProManager.paywallProductID,
                            selectionSource: "plan_card"
                        )
                    }
                }

                if shouldShowPaywallPlan(.annual, availableProductIDs: availableProductIDs) {
                    PlanOptionRow(
                        title: "Annual",
                        priceLabel: "\(annualPrice)/year",
                        badge: "Best Value",
                        isSelected: selectedPlan == .annual
                    ) {
                        selectedPlan = .annual
                        trackOfferSelected(
                            plan: "annual",
                            productID: ProManager.annualProductID,
                            selectionSource: "plan_card"
                        )
                    }
                }

                if shouldShowPaywallPlan(.monthly, availableProductIDs: availableProductIDs) {
                    PlanOptionRow(
                        title: "Monthly",
                        priceLabel: "\(monthlyPrice)/month",
                        badge: nil,
                        isSelected: selectedPlan == .monthly
                    ) {
                        selectedPlan = .monthly
                        trackOfferSelected(
                            plan: "monthly",
                            productID: ProManager.monthlyProductID,
                            selectionSource: "plan_card"
                        )
                    }
                }
            }
            .onChange(of: productsEligibilityKey) { _, _ in
                if shouldShowPaywallPlan(selectedPlan, availableProductIDs: availableProductIDs) {
                    return
                }
                if shouldShowPaywallPlan(.lifetime, availableProductIDs: availableProductIDs) {
                    selectedPlan = .lifetime
                } else if shouldShowPaywallPlan(.annual, availableProductIDs: availableProductIDs) {
                    selectedPlan = .annual
                } else if shouldShowPaywallPlan(.monthly, availableProductIDs: availableProductIDs) {
                    selectedPlan = .monthly
                }
            }
        }
    }

    /// Always visible above the home indicator: primary CTA + legal / dismiss affordances.
    @ViewBuilder
    private var paywallStickyChrome: some View {
        VStack(spacing: 12) {
            if availableProductIDs.isEmpty {
                Text("Loading subscription options from the App Store…")
                    .font(.footnote)
                    .foregroundColor(.textSecondary)
                    .multilineTextAlignment(.center)
            } else if !canPurchaseSelectedPlan {
                Text("This plan is not available in the App Store right now. Choose another plan or try again later.")
                    .font(.footnote)
                    .foregroundColor(.textSecondary)
                    .multilineTextAlignment(.center)
            }
            PrimaryButton(title: ctaButtonTitle) {
                guard canPurchaseSelectedPlan else { return }
                Task {
                    trackOfferSelected(
                        plan: planName(for: selectedPlan),
                        productID: selectedProductID,
                        selectionSource: "primary_cta"
                    )
                    await purchase(productID: selectedProductID)
                }
            }
            .opacity(canPurchaseSelectedPlan ? 1 : 0.55)
            .allowsHitTesting(canPurchaseSelectedPlan)
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(Color.white.opacity(0.95), lineWidth: 2.5)
            )

            Button("Restore purchase") {
                Task {
                    await restorePurchaseFromPaywall()
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
    }

    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                paywallScrollContent
                    .padding(.horizontal, 24)
                    .padding(.top, 8)
                    .padding(.bottom, 28)
            }
            .scrollIndicators(.hidden)

            Rectangle()
                .fill(Color.white.opacity(0.18))
                .frame(height: 1)
                .padding(.horizontal, 12)

            paywallStickyChrome
                .padding(.horizontal, 24)
                .padding(.top, 12)
                .padding(.bottom, 8)
                .frame(maxWidth: .infinity)
                .background(Color.backgroundDark)
                .safeAreaPadding(.bottom, 6)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(Color.backgroundDark)
        .task {
            let variant = PaywallExperimentVariants.label(defaultAnnual: defaultToAnnualExperiment)
            AnalyticsService.shared.setPaywallSurfaceContext(
                entryPoint: entryPoint.rawValue,
                experimentVariant: variant
            )
            let framing = AnalyticsService.shared.paywallValueFramingVariant()
            AnalyticsService.shared.track(AnalyticsEvents.paywallViewed, properties: [
                AnalyticsProperties.entryPoint: entryPoint.rawValue,
                AnalyticsProperties.paywallExperimentVariant: variant,
                AnalyticsProperties.paywallValueFramingVariant: framing,
            ])
            AnalyticsService.shared.trackSubscriptionFunnelStep(SubscriptionFunnelSteps.paywallViewed)
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
    private func restorePurchaseFromPaywall() async {
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

    @MainActor
    private func purchase(productID: String) async {
        AnalyticsService.shared.track(
            AnalyticsEvents.paywallPurchaseAttempt,
            properties: purchaseProperties(productID: productID)
        )
        AnalyticsService.shared.trackSubscriptionFunnelStep(
            SubscriptionFunnelSteps.purchaseFlowLaunched,
            properties: [
                AnalyticsProperties.productId: productID,
            ]
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
        AnalyticsService.shared.trackSubscriptionFunnelStep(
            SubscriptionFunnelSteps.purchaseSucceeded,
            properties: [AnalyticsProperties.productId: productID]
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
        let experimentVariant = PaywallExperimentVariants.label(defaultAnnual: defaultToAnnualExperiment)
        let framing = valueFramingVariant
        var properties: [String: Any] = [
            AnalyticsProperties.entryPoint: entryPoint.rawValue,
            AnalyticsProperties.productId: productID,
            AnalyticsProperties.paywallExperimentVariant: experimentVariant,
            AnalyticsProperties.paywallValueFramingVariant: framing,
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
            AnalyticsProperties.paywallValueFramingVariant: valueFramingVariant,
        ])
    }

    private func trackOfferSelected(plan: String, productID: String, selectionSource: String) {
        let experimentVariant = PaywallExperimentVariants.label(defaultAnnual: defaultToAnnualExperiment)
        let framing = AnalyticsService.shared.paywallValueFramingVariant()
        AnalyticsService.shared.track(AnalyticsEvents.paywallOfferSelect, properties: [
            AnalyticsProperties.entryPoint: entryPoint.rawValue,
            AnalyticsProperties.productId: productID,
            "plan": plan,
            AnalyticsProperties.paywallSelectionSource: selectionSource,
            AnalyticsProperties.paywallExperimentVariant: experimentVariant,
            AnalyticsProperties.paywallValueFramingVariant: framing,
        ])
        AnalyticsService.shared.trackSubscriptionFunnelStep(
            SubscriptionFunnelSteps.paywallPlanSelected,
            properties: [
                AnalyticsProperties.productId: productID,
                "plan": plan,
                AnalyticsProperties.paywallSelectionSource: selectionSource,
            ]
        )
    }

    private func planName(for plan: PaywallPlanSelection) -> String {
        switch plan {
        case .monthly:
            return "monthly"
        case .annual:
            return "annual"
        case .lifetime:
            return "lifetime"
        }
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
