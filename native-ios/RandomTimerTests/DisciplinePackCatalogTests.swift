import XCTest
@testable import RandomTimer

final class DisciplinePackCatalogTests: XCTestCase {
    func testAndroidPackIdsAreUnique() {
        let ids = DisciplinePackCatalog.androidProductIds
        XCTAssertEqual(ids.count, 4)
        XCTAssertEqual(Set(ids).count, 4)
        ids.forEach { XCTAssertTrue($0.hasPrefix("pack_")) }
    }

    func testIosIdsMapFromAndroid() {
        for androidId in DisciplinePackCatalog.androidProductIds {
            let iosId = DisciplinePackCatalog.iosProductId(forAndroidProductId: androidId)
            XCTAssertTrue(iosId.hasPrefix("com.iganapolsky.randomtimer.pack."))
        }
    }
}
