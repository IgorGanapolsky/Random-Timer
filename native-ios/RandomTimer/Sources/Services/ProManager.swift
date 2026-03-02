import os
import StoreKit

@MainActor
final class ProManager: ObservableObject {
    static let shared = ProManager()

    static nonisolated let productID = "com.iganapolsky.randomtimer.pro"

    @Published private(set) var isPro = false
    @Published private(set) var product: Product?

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
            let products = try await Product.products(for: [Self.productID])
            product = products.first
        } catch {
            Self.log.error("ProManager: failed to fetch products: \(error)")
        }
    }

    var formattedPrice: String {
        product?.displayPrice ?? "$4.99"
    }

    // MARK: - Purchase

    @discardableResult
    func purchase() async -> ProPurchaseResult {
        guard let product else {
            await fetchProduct()
            guard let product = self.product else { return .productUnavailable }
            return await doPurchase(product)
        }
        return await doPurchase(product)
    }

    private func doPurchase(_ product: Product) async -> ProPurchaseResult {
        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let transaction = try Self.checkVerified(verification)
                isPro = true
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
        if isPro {
            return .alreadyUnlocked
        }

        for await result in Transaction.currentEntitlements {
            if let transaction = try? Self.checkVerified(result),
               transaction.productID == Self.productID {
                isPro = true
                return .restored
            }
        }

        return isPro ? .alreadyUnlocked : .notFound
    }

    // MARK: - Transaction Listener

    private func listenForTransactions() -> Task<Void, Never> {
        Task.detached {
            for await result in Transaction.updates {
                if let transaction = try? Self.checkVerified(result),
                   transaction.productID == Self.productID {
                    await MainActor.run { [weak self] in self?.isPro = true }
                    await transaction.finish()
                }
            }
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

    /// Developer backdoor: unlock PRO without payment (8s long-press on paywall title).
    func forcePro() {
        isPro = true
        UserDefaults.standard.set(true, forKey: "forced_pro_status")
        AnalyticsService.shared.track("dev_force_pro")
        Self.log.notice("Developer override: Pro unlocked via backdoor")
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
