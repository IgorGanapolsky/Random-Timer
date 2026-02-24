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

    func purchase() async -> Bool {
        guard let product else {
            await fetchProduct()
            guard let product = self.product else { return false }
            return await doPurchase(product)
        }
        return await doPurchase(product)
    }

    private func doPurchase(_ product: Product) async -> Bool {
        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let transaction = try Self.checkVerified(verification)
                isPro = true
                await transaction.finish()
                return true
            case .userCancelled, .pending:
                return false
            @unknown default:
                return false
            }
        } catch {
            Self.log.error("ProManager: purchase failed: \(error)")
            return false
        }
    }

    // MARK: - Restore

    func restorePurchases() async {
        for await result in Transaction.currentEntitlements {
            if let transaction = try? Self.checkVerified(result),
               transaction.productID == Self.productID {
                isPro = true
                return
            }
        }
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
}

enum StoreError: Error {
    case failedVerification
}
