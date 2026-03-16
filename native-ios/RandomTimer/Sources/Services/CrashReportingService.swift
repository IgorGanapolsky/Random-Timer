import Foundation

#if canImport(FirebaseCrashlytics)
import FirebaseCrashlytics
#endif

/// Crash reporting service using Firebase Crashlytics
@MainActor
final class CrashReportingService {
    static let shared = CrashReportingService()

    private init() {}

    func initialize() {
#if canImport(FirebaseCrashlytics)
        Crashlytics.crashlytics().setCrashlyticsCollectionEnabled(true)
#endif
    }

    func setUserId(_ userId: String) {
#if canImport(FirebaseCrashlytics)
        Crashlytics.crashlytics().setUserID(userId)
#endif
    }

    func log(_ message: String) {
#if canImport(FirebaseCrashlytics)
        Crashlytics.crashlytics().log(message)
#endif
    }

    func setCustomValue(_ value: Any?, forKey key: String) {
#if canImport(FirebaseCrashlytics)
        Crashlytics.crashlytics().setCustomValue(value, forKey: key)
#endif
    }

    func record(error: Error) {
#if canImport(FirebaseCrashlytics)
        Crashlytics.crashlytics().record(error: error)
#endif
    }

    func sendUnsentReports() {
#if canImport(FirebaseCrashlytics)
        Crashlytics.crashlytics().sendUnsentReports()
#endif
    }
}
