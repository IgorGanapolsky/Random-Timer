import os
import StoreKit

@MainActor
final class ProManager: ObservableObject { // swiftlint:disable:this no_observable_object
    static let shared = ProManager()

    static nonisolated let baseProductID = "com.iganapolsky.randomtimer.pro"
    /// Legacy / future SKU — not guaranteed to exist in App Store Connect; keep for restore if ever shipped.
    static nonisolated let eliteProductID = "com.iganapolsky.randomtimer.elite"
    /// Monthly subscription — $3.99/month. Must be created in App Store Connect as an auto-renewable
    /// subscription before the paywall can complete a live purchase.
    static nonisolated let monthlyProductID = "com.iganapolsky.randomtimer.pro.monthly"
    /// Annual subscription — $29.99/year. Maps to the existing elite SKU billing period.
    static nonisolated let annualProductID = "com.iganapolsky.randomtimer.pro.annual"
    /// In-app paywall default product — one-time non-consumable Pro Upgrade.
    static nonisolated let paywallProductID = baseProductID
    static nonisolated var productIDs: Set<String> {
        [baseProductID, eliteProductID, monthlyProductID, annualProductID]
    }

    @Published private(set) var entitlementLevel: EntitlementLevel = .none
    @Published private(set) var products: [Product] = []
    private var debugOverrideActive = false

    var isPro: Bool { entitlementLevel.isPro }
    var isElite: Bool { entitlementLevel == .elite }

    /// True when the paywall product has a free introductory offer available for the current user.
    /// Uses StoreKit 2 `subscription?.introductoryOffer` — eligibility is managed automatically by App Store Connect.
    var hasFreeTrialOffer: Bool {
        guard let product = products.first(where: { $0.id == Self.paywallProductID }),
              let subscription = product.subscription
        else { return false }
        return subscription.introductoryOffer != nil
    }

    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "billing")

    private var transactionListener: Task<Void, Never>?
    private let launchOverrideEntitlementLevel: EntitlementLevel?

    private init() {
        let args = ProcessInfo.processInfo.arguments
        launchOverrideEntitlementLevel = Self.entitlementOverride(forLaunchArguments: args)
        if let launchOverrideEntitlementLevel {
            entitlementLevel = launchOverrideEntitlementLevel
        }

        if launchOverrideEntitlementLevel == nil {
            transactionListener = listenForTransactions()
            Task { await restorePurchases() }
        }
    }

    deinit {
        transactionListener?.cancel()
    }

    // MARK: - Fetch Product

    func fetchProduct() async {
        do {
            products = try await Product.products(for: Self.productIDs)
                .sorted(by: { $0.price < $1.price })
            if products.isEmpty {
                let ids = Self.productIDs
                Self.log.error("ProManager: products EMPTY for IDs: \(ids). Check ASC config.")
            }
        } catch {
            Self.log.error("ProManager: failed to fetch products: \(error)")
        }
    }

    func formattedPrice(for productID: String) -> String {
        if let match = products.first(where: { $0.id == productID }) {
            return match.displayPrice
        }
        // Fallback prices when store hasn't been configured yet
        switch productID {
        case Self.monthlyProductID: return "$3.99"
        case Self.annualProductID: return "$29.99"
        case Self.eliteProductID: return "$29.99"
        default: return "$4.99"
        }
    }

    // MARK: - Purchase

    @discardableResult
    func purchase(productID: String) async -> ProPurchaseResult {
        if products.isEmpty {
            await fetchProduct()
        }

        guard let product = products.first(where: { $0.id == productID }) else {
            return .productUnavailable
        }

        return await doPurchase(product)
    }

    private func doPurchase(_ product: Product) async -> ProPurchaseResult {
        // Capture trial eligibility before purchase so we can track it on success.
        let hasTrial = product.subscription?.introductoryOffer != nil
        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let transaction = try Self.checkVerified(verification)
                updateEntitlement(for: transaction.productID)
                await transaction.finish()
                // Track free trial start event when the user accepted a trial offer.
                if hasTrial {
                    AnalyticsService.shared.track(
                        AnalyticsEvents.freeTrialStarted,
                        properties: [AnalyticsProperties.productId: product.id]
                    )
                }
                return .success
            case .userCancelled:
                return .userCancelled
            case .pending:
                return .pending
            @unknown default:
                return .failed
            }
        } catch {
            Self.log.error("ProManager: purchase failed: \(error)")
            return .failed
        }
    }

    // MARK: - Restore

    @discardableResult
    func restorePurchases() async -> ProRestoreResult {
        if let launchOverrideEntitlementLevel {
            entitlementLevel = launchOverrideEntitlementLevel
            return .alreadyUnlocked
        }

        var highestLevel: EntitlementLevel = .none

        for await result in Transaction.currentEntitlements {
            if let transaction = try? Self.checkVerified(result) {
                let level = levelFor(productID: transaction.productID)
                if level == .elite {
                    highestLevel = .elite
                } else if level == .base && highestLevel == .none {
                    highestLevel = .base
                }
            }
        }

        let wasPro = isPro
        guard !debugOverrideActive else { return wasPro ? .alreadyUnlocked : .notFound }
        entitlementLevel = highestLevel

        if entitlementLevel.isPro {
            Task {
                await ProAudioPackStore.shared.refreshIfNeeded(isPro: true)
            }
        }

        if isPro && !wasPro {
            return .restored
        } else if isPro {
            return .alreadyUnlocked
        }

        return .notFound
    }

    // MARK: - Transaction Listener

    private func listenForTransactions() -> Task<Void, Never> {
        Task.detached {
            for await result in Transaction.updates {
                if let transaction = try? Self.checkVerified(result) {
                    let productID = transaction.productID
                    await MainActor.run { [weak self] in
                        guard self?.debugOverrideActive != true else { return }
                        self?.updateEntitlement(for: productID)
                    }
                    await transaction.finish()
                }
            }
        }
    }

    private func updateEntitlement(for productID: String) {
        let newLevel = levelFor(productID: productID)
        // Only upgrade, don't downgrade via this path (downgrades handled by restore/currentEntitlements)
        if newLevel == .elite {
            entitlementLevel = .elite
        } else if newLevel == .base && entitlementLevel == .none {
            entitlementLevel = .base
        }

        if entitlementLevel.isPro {
            Task {
                await ProAudioPackStore.shared.refreshIfNeeded(isPro: true)
            }
        }
    }

    private func levelFor(productID: String) -> EntitlementLevel {
        switch productID {
        case Self.eliteProductID: return .elite
        case Self.monthlyProductID: return .elite
        case Self.annualProductID: return .elite
        case Self.baseProductID: return .base
        default: return .none
        }
    }

    nonisolated static func entitlementOverride(forLaunchArguments args: [String]) -> EntitlementLevel? {
        if args.contains("-ui-test-elite") {
            return .elite
        }
        if args.contains("-ui-test-pro") {
            return .base
        }
        return nil
    }

    private nonisolated static func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified:
            throw StoreError.failedVerification
        case .verified(let safe):
            return safe
        }
    }

    // MARK: - Feature Gates

    static let maxSecondsFree = 300
    static let maxSecondsPro = 3600

    var maxSecondsLimit: Int {
        isPro ? Self.maxSecondsPro : Self.maxSecondsFree
    }

    var availableSounds: [SoundType] {
        isPro ? SoundType.allCases : SoundType.freeSounds
    }

    func unlockProForDebug() {
        entitlementLevel = .elite
        Self.log.notice("Developer override enabled: Pro unlocked via hidden hold gesture")
        Task {
            await ProAudioPackStore.shared.refreshIfNeeded(isPro: true)
        }
    }

    func unlockEliteForDebug() {
        entitlementLevel = .elite
        Self.log.notice("Developer override enabled: Elite unlocked via hidden hold gesture")
        Task {
            await ProAudioPackStore.shared.refreshIfNeeded(isPro: true)
        }
    }
}

enum StoreError: Error {
    case failedVerification
}

enum ProPurchaseResult: String {
    case success = "success"
    case userCancelled = "user_cancelled"
    case pending = "pending"
    case productUnavailable = "product_unavailable"
    case failed = "failed"
}

enum ProRestoreResult: String {
    case restored = "restored"
    case alreadyUnlocked = "already_unlocked"
    case notFound = "not_found"
}
