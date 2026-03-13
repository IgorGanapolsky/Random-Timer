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
    private var debugOverrideActive = false

    var isPro: Bool { entitlementLevel.isPro }
    var isElite: Bool { entitlementLevel == .elite }

    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "billing")

    private var transactionListener: Task<Void, Never>?

    private init() {
        transactionListener = listenForTransactions()
        Task { await restorePurchases() }
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
            return .productUnavailable
        }
        
        return await doPurchase(product)
    }

    private func doPurchase(_ product: Product) async -> ProPurchaseResult {
        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let transaction = try Self.checkVerified(verification)
                updateEntitlement(for: transaction.productID)
                await transaction.finish()
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
    }

    private func levelFor(productID: String) -> EntitlementLevel {
        switch productID {
        case Self.eliteProductID: return .elite
        case Self.baseProductID: return .base
        default: return .none
        }
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
    }
    
    func unlockEliteForDebug() {
        entitlementLevel = .elite
        Self.log.notice("Developer override enabled: Elite unlocked via hidden hold gesture")
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
