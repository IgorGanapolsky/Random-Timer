import Foundation
import os
import StoreKit

@MainActor
final class ProManager: ObservableObject {
    static let shared = ProManager()

    static nonisolated let baseProductID = "com.iganapolsky.randomtimer.pro"
    static nonisolated let eliteProductID = "com.iganapolsky.randomtimer.elite"
    static nonisolated var productIDs: Set<String> { [baseProductID, eliteProductID] }

    @Published private(set) var entitlementLevel: EntitlementLevel = .none
    @Published private(set) var products: [Product] = []
    @Published private(set) var newProUnlockEventID: Int = 0
    private var debugOverrideActive = false

    var isPro: Bool { entitlementLevel.isPro }
    var isElite: Bool { entitlementLevel == .elite }

    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "billing")

    private var transactionListener: Task<Void, Never>?
    private let launchOverrideEntitlementLevel: EntitlementLevel?
    private let defaults = UserDefaults.standard

    private enum Keys {
        static let pendingPaywallRangeDefault = "pending_paywall_range_default"
    }

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
        } catch {
            Self.log.error("ProManager: failed to fetch products: \(error)")
        }
    }

    func formattedPrice(for productID: String) -> String {
        products.first(where: { $0.id == productID })?.displayPrice ?? (productID == Self.eliteProductID ? "$29.99/yr" : "$4.99")
    }

    // MARK: - Purchase

    @discardableResult
    func purchase(productID: String) async -> ProPurchaseResult {
        if products.isEmpty {
            await fetchProduct()
        }

        guard let product = products.first(where: { $0.id == productID }) else {
            setPendingPaywallRangeDefault(false)
            return .productUnavailable
        }

        if !isPro {
            setPendingPaywallRangeDefault(true)
        }
        return await doPurchase(product)
    }

    private func doPurchase(_ product: Product) async -> ProPurchaseResult {
        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let transaction = try Self.checkVerified(verification)
                let wasPro = isPro
                updateEntitlement(for: transaction.productID)
                emitPendingNewProUnlockIfNeeded(wasPro: wasPro)
                await transaction.finish()
                return .success
            case .userCancelled:
                setPendingPaywallRangeDefault(false)
                return .userCancelled
            case .pending:
                return .pending
            @unknown default:
                setPendingPaywallRangeDefault(false)
                return .failed
            }
        } catch {
            Self.log.error("ProManager: purchase failed: \(error)")
            setPendingPaywallRangeDefault(false)
            return .failed
        }
    }

    // MARK: - Restore

    @discardableResult
    func restorePurchases(fromPaywall: Bool = false) async -> ProRestoreResult {
        if let launchOverrideEntitlementLevel {
            entitlementLevel = launchOverrideEntitlementLevel
            return .alreadyUnlocked
        }

        if fromPaywall && !isPro {
            setPendingPaywallRangeDefault(true)
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
        guard !debugOverrideActive else {
            if !wasPro {
                setPendingPaywallRangeDefault(false)
            }
            return wasPro ? .alreadyUnlocked : .notFound
        }
        entitlementLevel = highestLevel

        if entitlementLevel.isPro {
            Task {
                await ProAudioPackStore.shared.refreshIfNeeded(isPro: true)
            }
        }

        emitPendingNewProUnlockIfNeeded(wasPro: wasPro)
        if !isPro {
            setPendingPaywallRangeDefault(false)
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
                        let wasPro = self?.isPro ?? false
                        self?.updateEntitlement(for: productID)
                        self?.emitPendingNewProUnlockIfNeeded(wasPro: wasPro)
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
        let wasPro = isPro
        if !wasPro {
            setPendingPaywallRangeDefault(true)
        }
        entitlementLevel = .elite
        Self.log.notice("Developer override enabled: Pro unlocked via hidden hold gesture")
        Task {
            await ProAudioPackStore.shared.refreshIfNeeded(isPro: true)
        }
        emitPendingNewProUnlockIfNeeded(wasPro: wasPro)
    }
    
    func unlockEliteForDebug() {
        let wasPro = isPro
        if !wasPro {
            setPendingPaywallRangeDefault(true)
        }
        entitlementLevel = .elite
        Self.log.notice("Developer override enabled: Elite unlocked via hidden hold gesture")
        Task {
            await ProAudioPackStore.shared.refreshIfNeeded(isPro: true)
        }
        emitPendingNewProUnlockIfNeeded(wasPro: wasPro)
    }

    private func emitPendingNewProUnlockIfNeeded(wasPro: Bool) {
        guard pendingPaywallRangeDefault, isPro else { return }
        if !wasPro {
            newProUnlockEventID += 1
        }
        setPendingPaywallRangeDefault(false)
    }

    private var pendingPaywallRangeDefault: Bool {
        defaults.bool(forKey: Keys.pendingPaywallRangeDefault)
    }

    private func setPendingPaywallRangeDefault(_ pending: Bool) {
        defaults.set(pending, forKey: Keys.pendingPaywallRangeDefault)
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
