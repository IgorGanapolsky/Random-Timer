import Foundation

/// Loads `releaseMonth` from the hosted Pro audio runtime manifest URL in Info.plist.
final class ProMonthlyContentManifestProvider: Sendable {
    static let shared = ProMonthlyContentManifestProvider()

    private let session: URLSession
    private let manifestURL: URL?

    init(bundle: Bundle = .main, session: URLSession = .shared) {
        self.session = session
        if let urlString = bundle.object(forInfoDictionaryKey: "PRO_AUDIO_MANIFEST_URL") as? String,
           let url = URL(string: urlString.trimmingCharacters(in: .whitespacesAndNewlines)),
           !urlString.isEmpty {
            manifestURL = url
        } else {
            manifestURL = nil
        }
    }

    func fetchReleaseMonth() async -> String? {
        guard let manifestURL else { return nil }
        do {
            let (data, response) = try await session.data(from: manifestURL)
            guard let http = response as? HTTPURLResponse, (200 ... 299).contains(http.statusCode) else {
                return nil
            }
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            let month = json?["releaseMonth"] as? String
            let trimmed = month?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            return trimmed.isEmpty ? nil : trimmed
        } catch {
            return nil
        }
    }
}
