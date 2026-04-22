import Foundation

struct AppBootstrapPlan: Equatable {
    let shouldInitializeFirebase: Bool
    let shouldInitializeAnalytics: Bool
    let logMessage: String?

    static func resolve(
        skipHostedTests: Bool,
        hasBundledFirebaseConfig: Bool,
    ) -> Self {
        if skipHostedTests {
            return Self(
                shouldInitializeFirebase: false,
                shouldInitializeAnalytics: false,
                logMessage: "Skipping Firebase and analytics initialization for hosted tests."
            )
        }

        if !hasBundledFirebaseConfig {
            return Self(
                shouldInitializeFirebase: false,
                shouldInitializeAnalytics: true,
                logMessage: "Skipping Firebase initialization because GoogleService-Info.plist is not bundled."
            )
        }

        return Self(
            shouldInitializeFirebase: true,
            shouldInitializeAnalytics: true,
            logMessage: nil
        )
    }
}
