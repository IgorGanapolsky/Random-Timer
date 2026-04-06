import XCTest
@testable import RandomTimer

final class ActivationDefaultsTests: XCTestCase {

    func testDefaultMinSecondsIsFiveForActivationFirstQuickStart() {
        let config = TimerConfig.default
        XCTAssertEqual(config.minSeconds, 5)
    }

    func testDefaultMaxSecondsIs30ForActivationFirstQuickStart() {
        let config = TimerConfig.default
        XCTAssertEqual(config.maxSeconds, 30)
    }

    func testDefaultConfigProducesValidDurationRange() {
        let config = TimerConfig.default
        XCTAssertGreaterThan(config.maxSeconds, config.minSeconds)
        XCTAssertGreaterThanOrEqual(config.maxSeconds - config.minSeconds, 5)
    }

    func testDefaultMinDurationIsFiveSeconds() {
        let config = TimerConfig.default
        XCTAssertEqual(config.minDuration, 5.0, accuracy: 0.001)
    }

    func testDefaultMaxDurationIs30Seconds() {
        let config = TimerConfig.default
        XCTAssertEqual(config.maxDuration, 30.0, accuracy: 0.001)
    }

    func testExplicitZeroMinClampsToSafeFloor() {
        let config = TimerConfig(minSeconds: 0, maxSeconds: 60)
        XCTAssertEqual(config.minSeconds, 5)
    }

    func testExplicit300MaxStillAllowed() {
        let config = TimerConfig(minSeconds: 5, maxSeconds: 300)
        XCTAssertEqual(config.maxSeconds, 300)
    }

    func testCodableRoundTripPreservesNewDefaults() throws {
        let config = TimerConfig.default
        let data = try JSONEncoder().encode(config)
        let decoded = try JSONDecoder().decode(TimerConfig.self, from: data)
        XCTAssertEqual(decoded.minSeconds, 5)
        XCTAssertEqual(decoded.maxSeconds, 30)
    }

    func testEmptyJsonDecodesToNewDefaults() throws {
        let data = Data("{}".utf8)
        let decoded = try JSONDecoder().decode(TimerConfig.self, from: data)
        XCTAssertEqual(decoded.minSeconds, 5)
        XCTAssertEqual(decoded.maxSeconds, 30)
    }

    func testMaxSecondsFreeUnchangedAt300() {
        XCTAssertEqual(TimerConfig.maxSecondsFree, 300)
    }

    func testMaxSecondsProUnchangedAt3600() {
        XCTAssertEqual(TimerConfig.maxSecondsPro, 3600)
    }
}
