import XCTest
@testable import RandomTimer

final class ProMonthlyContentMessagingTests: XCTestCase {
    func testMonthLabelFormatsReleaseMonth() {
        XCTAssertEqual(ProMonthlyContentMessaging.monthLabel(releaseMonth: "2026-05"), "May 2026")
    }

    func testNotificationCopyUsesDynamicMonth() {
        let copy = ProMonthlyContentMessaging.notificationCopy(releaseMonth: "2026-05")
        XCTAssertEqual(copy.title, "New Audio Drops for May 2026")
        XCTAssertTrue(copy.body.contains("Sound Arsenal"))
    }
}
