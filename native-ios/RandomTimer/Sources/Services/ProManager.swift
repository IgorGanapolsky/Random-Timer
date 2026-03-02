import os
import StoreKit

@MainActor
final class ProManager: ObservableObject {
    static let shared = ProManager()

    static nonisolated let baseProductID = "com.iganapolsky.randomtimer.pro"
    static nonisolated let eliteProductID = "com.iganapolsky.randomtimer.elite"

    @Published private(set) var entitlementLevel: EntitlementLevel = .none
    @Published private(set) var products: [Product] = []

    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "billing")
    private let forcedProKey = "forced_pro_status"
    private let entitlementKey = "user_entitlement_level"

    private var transactionListener: Task<Void, Never>?

    private init() {
        let savedLevel = UserDefaults.standard.integer(forKey: entitlementKey)
        entitlementLevel = EntitlementLevel(rawValue: savedLevel) ?? .none
        
        if entitlementLevel == .none && UserDefaults.standard.bool(forKey: forcedProKey) {
            entitlementLevel = .base
        }
        
        transactionListener = listenForTransactions()
        Task { 
            await fetchProducts()
            await restorePurchases() 
        }
    }

    deinit {
        transactionListener?.cancel()
    }

    var isPro: Bool { entitlementLevel >= .base }
    var isElite: Bool { entitlementLevel == .elite }

    func fetchProducts() async {
        do {
            let storeProducts = try await Product.products(for: [Self.baseProductID, Self.eliteProductID])
            products = storeProducts.sorted(by: { $0.price < $1.price })
        } catch {
            Self.log.error("ProManager: failed to fetch products: \(error)")
        }
    }

    @discardableResult
    func purchase(productID: String) async -> ProPurchaseResult {
        guard let product = products.first(where: { $0.id == productID }) else {
            await fetchProducts()
            guard let product = products.first(where: { $0.id == productID }) else {
                return .productUnavailable
            }
            return await doPurchase(product)
        }
        return await doPurchase(product)
    }

    private func doPurchase(_ product: Product) async -> ProPurchaseResult {
        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let transaction = try checkVerified(verification)
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

    @discardableResult
    func restorePurchases() async -> ProRestoreResult {
        var restored = false
        for await result in Transaction.currentEntitlements {
            if let transaction = try? checkVerified(result) {
                updateEntitlement(for: transaction.productID)
                restored = true
            }
        }
        return restored ? .restored : .notFound
    }

    private func updateEntitlement(for productID: String) {
        if productID == Self.eliteProductID {
            entitlementLevel = .elite
        } else if productID == Self.baseProductID {
            if entitlementLevel < .base {
                entitlementLevel = .base
            }
        }
        UserDefaults.standard.set(entitlementLevel.rawValue, forKey: entitlementKey)
    }

    private func listenForTransactions() -> Task<Void, Never> {
        Task.detached {
            for await result in Transaction.updates {
                await MainActor.run { [weak self] in
                    guard let self = self else { return }
                    if let transaction = try? self.checkVerified(result) {
                        self.updateEntitlement(for: transaction.productID)
                        Task { await transaction.finish() }
                    }
                }
            }
        }
    }

    func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified: throw StoreError.failedVerification
        case .verified(let safe): return safe
        }
    }

    func forcePro() {
        entitlementLevel = .elite
        UserDefaults.standard.set(entitlementLevel.rawValue, forKey: entitlementKey)
        Self.log.info("ProManager: Elite status forced via secret override.")
    }

    var maxSecondsLimit: Int { isPro ? TimerConfig.maxSecondsPro : TimerConfig.maxSecondsFree }
    var availableSounds: [SoundType] { isPro ? SoundType.allCases : SoundType.freeSounds }
    
    func formattedPrice(for id: String) -> String {
        return products.first(where: { $0.id == id })?.displayPrice ?? (id == Self.eliteProductID ? "$19.99" : "$4.99")
    }
}

enum StoreError: Error {
    case failedVerification
}
