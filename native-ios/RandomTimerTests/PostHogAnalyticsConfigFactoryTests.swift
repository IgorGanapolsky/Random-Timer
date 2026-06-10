import XCTest
@testable import RandomTimer

final class PostHogAnalyticsConfigFactoryTests: XCTestCase {
    func testErrorTrackingAutocaptureEnabledForProductionUsers() {
        let config = PostHogAnalyticsConfigFactory.make(apiKey: "phc_test", isInternalUser: false)
        XCTAssertTrue(config.errorTrackingConfig.autoCapture)
    }

    func testErrorTrackingAutocaptureDisabledForInternalUsers() {
        let config = PostHogAnalyticsConfigFactory.make(apiKey: "phc_test", isInternalUser: true)
        XCTAssertFalse(config.errorTrackingConfig.autoCapture)
    }
}
