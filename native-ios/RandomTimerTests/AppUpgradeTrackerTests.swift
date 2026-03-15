import XCTest
@testable import RandomTimer

final class AppUpgradeTrackerTests: XCTestCase {

    private func makeIsolatedDefaults() -> UserDefaults {
        let suiteName = "AppUpgradeTrackerTests-\(UUID().uuidString)"
        guard let defaults = UserDefaults(suiteName: suiteName) else {
            XCTFail("Failed to create UserDefaults suite for tests")
            return .standard
        }
        defaults.removePersistentDomain(forName: suiteName)
        return defaults
    }

    func testFirstLaunchWhenNoStoredVersionOrBuild() {
        let defaults = makeIsolatedDefaults()
        let tracker = AppUpgradeTracker(defaults: defaults)

        let info = tracker.evaluateLaunch(currentVersion: "1.0", currentBuild: "1")

        XCTAssertTrue(info.isFirstLaunch)
        XCTAssertFalse(info.isUpgrade)
        XCTAssertNil(info.fromVersion)
        XCTAssertNil(info.fromBuild)
        XCTAssertEqual(info.toVersion, "1.0")
        XCTAssertEqual(info.toBuild, "1")
    }

    func testSecondLaunchSameVersionIsNotUpgrade() {
        let defaults = makeIsolatedDefaults()
        let tracker = AppUpgradeTracker(defaults: defaults)

        _ = tracker.evaluateLaunch(currentVersion: "1.0", currentBuild: "1")
        let second = tracker.evaluateLaunch(currentVersion: "1.0", currentBuild: "1")

        XCTAssertFalse(second.isFirstLaunch)
        XCTAssertFalse(second.isUpgrade)
        XCTAssertEqual(second.fromVersion, "1.0")
        XCTAssertEqual(second.fromBuild, "1")
        XCTAssertEqual(second.toVersion, "1.0")
        XCTAssertEqual(second.toBuild, "1")
    }

    func testVersionChangeMarksUpgrade() {
        let defaults = makeIsolatedDefaults()
        let tracker = AppUpgradeTracker(defaults: defaults)

        _ = tracker.evaluateLaunch(currentVersion: "1.0", currentBuild: "1")
        let upgraded = tracker.evaluateLaunch(currentVersion: "1.1", currentBuild: "1")

        XCTAssertFalse(upgraded.isFirstLaunch)
        XCTAssertTrue(upgraded.isUpgrade)
        XCTAssertEqual(upgraded.fromVersion, "1.0")
        XCTAssertEqual(upgraded.toVersion, "1.1")
        XCTAssertEqual(upgraded.fromBuild, "1")
        XCTAssertEqual(upgraded.toBuild, "1")
    }

    func testBuildChangeMarksUpgrade() {
        let defaults = makeIsolatedDefaults()
        let tracker = AppUpgradeTracker(defaults: defaults)

        _ = tracker.evaluateLaunch(currentVersion: "1.0", currentBuild: "1")
        let upgraded = tracker.evaluateLaunch(currentVersion: "1.0", currentBuild: "2")

        XCTAssertFalse(upgraded.isFirstLaunch)
        XCTAssertTrue(upgraded.isUpgrade)
        XCTAssertEqual(upgraded.fromVersion, "1.0")
        XCTAssertEqual(upgraded.toVersion, "1.0")
        XCTAssertEqual(upgraded.fromBuild, "1")
        XCTAssertEqual(upgraded.toBuild, "2")
    }
}

