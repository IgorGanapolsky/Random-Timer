import Foundation
import FirebaseCrashlytics

/// Crash reporting service using Firebase Crashlytics
final class CrashReportingService: @unchecked Sendable {
    static let shared = CrashReportingService()

    private init() {}

    func initialize() {
        // Crashlytics is automatically initialized via GoogleService-Info.plist
        // Enable collection
        Crashlytics.crashlytics().setCrashlyticsCollectionEnabled(true)
    }

    func setUserId(_ userId: String) {
        Crashlytics.crashlytics().setUserID(userId)
    }

    func log(_ message: String) {
        Crashlytics.crashlytics().log(message)
    }

    func setCustomValue(_ value: Any?, forKey key: String) {
        Crashlytics.crashlytics().setCustomValue(value, forKey: key)
    }

    func record(error: Error) {
        Crashlytics.crashlytics().record(error: error)
    }

    func sendUnsentReports() {
        Crashlytics.crashlytics().sendUnsentReports()
    }
}
