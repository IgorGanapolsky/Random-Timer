import XCTest
@testable import RandomTimer

final class ActivationDefaultsTests: XCTestCase {

    func testDefaultMinSecondsIs30ForQuickStart() {
        let config = TimerConfig.default
        XCTAssertEqual(config.minSeconds, 30)
    }

    func testDefaultMaxSecondsIs120ForQuickStart() {
        let config = TimerConfig.default
        XCTAssertEqual(config.maxSeconds, 120)
    }

    func testDefaultConfigProducesValidDurationRange() {
        let config = TimerConfig.default
        XCTAssertGreaterThan(config.maxSeconds, config.minSeconds)
        XCTAssertGreaterThanOrEqual(config.maxSeconds - config.minSeconds, 5)
    }

    func testDefaultMinDurationIs30Seconds() {
        let config = TimerConfig.default
        XCTAssertEqual(config.minDuration, 30.0, accuracy: 0.001)
    }

    func testDefaultMaxDurationIs120Seconds() {
        let config = TimerConfig.default
        XCTAssertEqual(config.maxDuration, 120.0, accuracy: 0.001)
    }

    func testExplicitZeroMinStillAllowed() {
        let config = TimerConfig(minSeconds: 0, maxSeconds: 60)
        XCTAssertEqual(config.minSeconds, 0)
    }

    func testExplicit300MaxStillAllowed() {
        let config = TimerConfig(minSeconds: 0, maxSeconds: 300)
        XCTAssertEqual(config.maxSeconds, 300)
    }

    func testCodableRoundTripPreservesNewDefaults() throws {
        let config = TimerConfig.default
        let data = try JSONEncoder().encode(config)
        let decoded = try JSONDecoder().decode(TimerConfig.self, from: data)
        XCTAssertEqual(decoded.minSeconds, 30)
        XCTAssertEqual(decoded.maxSeconds, 120)
    }

    func testEmptyJsonDecodesToNewDefaults() throws {
        let data = Data("{}".utf8)
        let decoded = try JSONDecoder().decode(TimerConfig.self, from: data)
        XCTAssertEqual(decoded.minSeconds, 30)
        XCTAssertEqual(decoded.maxSeconds, 120)
    }

    func testMaxSecondsFreeUnchangedAt300() {
        XCTAssertEqual(TimerConfig.maxSecondsFree, 300)
    }

    func testMaxSecondsProUnchangedAt3600() {
        XCTAssertEqual(TimerConfig.maxSecondsPro, 3600)
    }
}
