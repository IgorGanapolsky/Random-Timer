import CryptoKit
import Foundation

struct RuntimeConfigurationSnapshot: Equatable {
    let defaultConfig: TimerConfig
    let configSource: String
    let configVersion: String
    let experiments: [String: String]

    static let bundled = RuntimeConfigurationSnapshot(
        defaultConfig: .default,
        configSource: "bundled",
        configVersion: "bundled",
        experiments: [:]
    )

    var analyticsProperties: [String: Any] {
        var properties: [String: Any] = [
            AnalyticsProperties.runtimeConfigSource: configSource,
            AnalyticsProperties.runtimeConfigVersion: configVersion,
        ]
        experiments.forEach { key, value in
            properties["experiment_\(key)"] = value
        }
        return properties
    }
}

struct RuntimeConfigurationPayload: Decodable, Equatable {
    let configVersion: String
    let defaultTimerConfig: TimerConfig
    let experiments: [RuntimeExperimentDefinition]

    func toSnapshot(distinctId: String) -> RuntimeConfigurationSnapshot {
        RuntimeConfigurationSnapshot(
            defaultConfig: defaultTimerConfig,
            configSource: "insforge_storage",
            configVersion: configVersion,
            experiments: RuntimeExperimentAssigner.assign(distinctId: distinctId, experiments: experiments)
        )
    }
}

struct RuntimeExperimentDefinition: Decodable, Equatable {
    let key: String
    let variants: [RuntimeExperimentVariant]
}

struct RuntimeExperimentVariant: Decodable, Equatable {
    let key: String
    let rolloutPercent: Int
}

enum RuntimeExperimentAssigner {
    static func assign(
        distinctId: String,
        experiments: [RuntimeExperimentDefinition]
    ) -> [String: String] {
        Dictionary(
            uniqueKeysWithValues: experiments.compactMap { definition in
                guard let variant = chooseVariant(distinctId: distinctId, definition: definition) else {
                    return nil
                }
                return (definition.key, variant)
            }
        )
    }

    private static func chooseVariant(
        distinctId: String,
        definition: RuntimeExperimentDefinition
    ) -> String? {
        guard definition.variants.isEmpty == false else { return nil }

        let bucket = bucketFor(seed: "\(definition.key):\(distinctId)")
        var cumulative = 0
        for variant in definition.variants {
            cumulative += max(0, min(100, variant.rolloutPercent))
            if bucket < cumulative {
                return variant.key
            }
        }
        return nil
    }

    private static func bucketFor(seed: String) -> Int {
        let digest = SHA256.hash(data: Data(seed.utf8))
        let value = digest.prefix(8).reduce(UInt64(0)) { partial, byte in
            (partial << 8) | UInt64(byte)
        }
        return Int(value % 100)
    }
}

@MainActor
final class RuntimeConfigurationService {
    private(set) var snapshot: RuntimeConfigurationSnapshot = .bundled

    private let session: URLSession
    private var didRefresh = false

    init(session: URLSession = .shared) {
        self.session = session
    }

    func refreshIfNeeded(distinctId: String?) async {
        guard didRefresh == false else { return }
        didRefresh = true
        guard
            let distinctId,
            distinctId.isEmpty == false,
            let objectURL,
            apiKey.isEmpty == false
        else {
            return
        }

        do {
            let payload = try await fetchPayload(from: objectURL, apiKey: apiKey)
            snapshot = payload.toSnapshot(distinctId: distinctId)
        } catch {
            // Optional runtime config. Fall back silently to bundled defaults.
        }
    }

    func applyPayloadForTesting(_ payload: RuntimeConfigurationPayload, distinctId: String) {
        snapshot = payload.toSnapshot(distinctId: distinctId)
    }

    private var objectURL: URL? {
        guard
            let raw = Bundle.main.object(forInfoDictionaryKey: "INSFORGE_API_BASE_URL") as? String,
            raw.isEmpty == false
        else {
            return nil
        }
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines).trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        return URL(string: "\(trimmed)/api/storage/buckets/training_assets/objects/runtime/mobile-runtime-config.json")
    }

    private var apiKey: String {
        Bundle.main.object(forInfoDictionaryKey: "INSFORGE_API_KEY") as? String ?? ""
    }

    private func fetchPayload(from objectURL: URL, apiKey: String) async throws -> RuntimeConfigurationPayload {
        var request = URLRequest(url: objectURL)
        request.httpMethod = "GET"
        request.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 5

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(RuntimeConfigurationPayload.self, from: data)
    }
}
