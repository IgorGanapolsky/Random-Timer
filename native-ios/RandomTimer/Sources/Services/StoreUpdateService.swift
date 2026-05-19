import Foundation

/// Service for checking if a newer version of the app is available in the App Store.
final class StoreUpdateService {
    private let appId = "6758355312"
    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    /**
     Checks the App Store for a newer version of the app.
     - Returns: The version string of the update if available, otherwise nil.
     */
    func checkForUpdates(
        currentVersion: String? = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String
    ) async -> String? {
        let urlString = "https://itunes.apple.com/lookup?id=\(appId)&country=us"
        guard let url = URL(string: urlString) else { return nil }

        do {
            let (data, _) = try await session.data(from: url)
            let lookup = try JSONDecoder().decode(ITunesLookup.self, from: data)
            guard let storeVersion = lookup.results.first?.version else { return nil }

            if let currentVersion, isVersion(storeVersion, newerThan: currentVersion) {
                return storeVersion
            }
        } catch {
            // Silence errors in production background checks to avoid interrupting the user.
        }
        return nil
    }

    private func isVersion(_ v1: String, newerThan v2: String) -> Bool {
        return v1.compare(v2, options: .numeric) == .orderedDescending
    }
}

private struct ITunesLookup: Codable {
    let results: [Result]
    struct Result: Codable {
        let version: String
    }
}
