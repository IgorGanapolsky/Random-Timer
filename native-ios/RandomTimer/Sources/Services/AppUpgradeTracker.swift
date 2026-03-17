import Foundation

/// Immutable snapshot describing this launch in relation to past installs.
struct AppUpgradeInfo: Equatable {
    let isFirstLaunch: Bool
    let isUpgrade: Bool
    let fromVersion: String?
    let fromBuild: String?
    let toVersion: String
    let toBuild: String
}

/// Pure, testable helper that detects when the app was upgraded between launches.
///
/// This type owns ONLY the UserDefaults read/write logic; callers are responsible
/// for wiring the resulting `AppUpgradeInfo` into Crashlytics / analytics.
final class AppUpgradeTracker {
    private enum Keys {
        static let lastVersion = "app_last_version"
        static let lastBuild = "app_last_build"
    }

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    /// Compute upgrade information for this launch and persist the current version/build.
    ///
    /// - Parameters:
    ///   - currentVersion: CFBundleShortVersionString (e.g. "1.2.3").
    ///   - currentBuild:   CFBundleVersion (e.g. "45").
    func evaluateLaunch(
        currentVersion: String,
        currentBuild: String
    ) -> AppUpgradeInfo {
        let previousVersion = defaults.string(forKey: Keys.lastVersion)
        let previousBuild = defaults.string(forKey: Keys.lastBuild)

        let isFirstLaunch = (previousVersion == nil || previousBuild == nil)
        let isUpgrade: Bool

        if isFirstLaunch {
            isUpgrade = false
        } else {
            // Treat any change in either version or build as an upgrade.
            isUpgrade = (previousVersion != currentVersion) || (previousBuild != currentBuild)
        }

        // Persist the new version/build for the next launch BEFORE returning.
        defaults.set(currentVersion, forKey: Keys.lastVersion)
        defaults.set(currentBuild, forKey: Keys.lastBuild)

        return AppUpgradeInfo(
            isFirstLaunch: isFirstLaunch,
            isUpgrade: isUpgrade,
            fromVersion: previousVersion,
            fromBuild: previousBuild,
            toVersion: currentVersion,
            toBuild: currentBuild
        )
    }
}
