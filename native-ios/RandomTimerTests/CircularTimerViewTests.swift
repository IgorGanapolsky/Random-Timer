import XCTest
@testable import RandomTimer

/// Tests for CircularTimerView animation math functions.
/// Must match Android CircularTimerTest animation parity assertions.
@MainActor
final class CircularTimerViewTests: XCTestCase {

    // -- fastOutSlowIn easing curve tests --

    func testFastOutSlowInAtZero() {
        let result = CircularTimerView.fastOutSlowIn(0.0)
        XCTAssertEqual(result, 0.0, accuracy: 0.001)
    }

    func testFastOutSlowInAtOne() {
        let result = CircularTimerView.fastOutSlowIn(1.0)
        XCTAssertEqual(result, 1.0, accuracy: 0.001)
    }

    func testFastOutSlowInIsMonotonicallyIncreasing() {
        var previous = 0.0
        for i in 1...100 {
            let t = Double(i) / 100.0
            let result = CircularTimerView.fastOutSlowIn(t)
            XCTAssertGreaterThanOrEqual(result, previous, "fastOutSlowIn must be monotonically increasing at t=\(t)")
            previous = result
        }
    }

    func testFastOutSlowInMidpoint() {
        // CubicBezier(0.4, 0.0, 0.2, 1.0) at t=0.5 should be roughly 0.8
        // (it's a fast-out-slow-in curve, so it's past halfway by t=0.5)
        let result = CircularTimerView.fastOutSlowIn(0.5)
        XCTAssertGreaterThan(result, 0.5)
        XCTAssertLessThan(result, 1.0)
    }

    // -- computePulseT tests --

    func testComputePulseTAtZeroIsZero() {
        let result = CircularTimerView.computePulseT(0.0)
        XCTAssertEqual(result, 0.0, accuracy: 0.001)
    }

    func testComputePulseTAtHalfIsOne() {
        // At cycle=0.5, the pulse should be at its peak (1.0)
        // because first half goes 0→1 and second half goes 1→0
        let result = CircularTimerView.computePulseT(0.5)
        XCTAssertEqual(result, 1.0, accuracy: 0.01)
    }

    func testComputePulseTAtOneReturnsToZero() {
        // At cycle=0.999... (near 1.0), should be back near 0
        let result = CircularTimerView.computePulseT(0.999)
        XCTAssertEqual(result, 0.0, accuracy: 0.05)
    }

    func testComputePulseTMirrorsAroundHalf() {
        // computePulseT uses fastOutSlowIn in both halves.
        // First half: fastOutSlowIn(cycle * 2) going up
        // Second half: 1 - fastOutSlowIn((cycle - 0.5) * 2) going down
        // So computePulseT(0.25) = fastOutSlowIn(0.5)
        //    computePulseT(0.75) = 1 - fastOutSlowIn(0.5)
        // They sum to 1.0, not equal each other (since the easing is nonlinear)
        let firstQuarter = CircularTimerView.computePulseT(0.25)
        let thirdQuarter = CircularTimerView.computePulseT(0.75)
        XCTAssertEqual(firstQuarter + thirdQuarter, 1.0, accuracy: 0.01)
    }

    func testComputePulseTFirstHalfIncreases() {
        var previous = 0.0
        for i in 1...49 {
            let cycle = Double(i) / 100.0
            let result = CircularTimerView.computePulseT(cycle)
            XCTAssertGreaterThanOrEqual(result, previous, "Pulse must increase in first half at cycle=\(cycle)")
            previous = result
        }
    }

    func testComputePulseTSecondHalfDecreases() {
        var previous = 1.0
        for i in 51...99 {
            let cycle = Double(i) / 100.0
            let result = CircularTimerView.computePulseT(cycle)
            XCTAssertLessThanOrEqual(result, previous, "Pulse must decrease in second half at cycle=\(cycle)")
            previous = result
        }
    }

    func testComputePulseTRangeIsBounded() {
        // Pulse should always be in [0, 1]
        for i in 0...100 {
            let cycle = Double(i) / 100.0
            let result = CircularTimerView.computePulseT(cycle)
            XCTAssertGreaterThanOrEqual(result, 0.0, "Pulse out of range at cycle=\(cycle)")
            XCTAssertLessThanOrEqual(result, 1.0, "Pulse out of range at cycle=\(cycle)")
        }
    }

    func testPausedStatusDoesNotBreatheText() {
        XCTAssertFalse(CircularTimerView.shouldBreatheText(for: .paused))
        XCTAssertTrue(CircularTimerView.shouldResetTextBreathing(for: .paused))
    }

    func testRunningStatusBreathesText() {
        XCTAssertTrue(CircularTimerView.shouldBreatheText(for: .running))
        XCTAssertFalse(CircularTimerView.shouldResetTextBreathing(for: .running))
    }

    func testLoopBadgeTextShowsOffStateWhenDisabled() {
        let result = ActiveTimerScreen.loopBadgeText(enabled: false, repeatRounds: 4, roundCount: 2)
        XCTAssertEqual(result, "Loop Off")
    }

    func testLoopBadgeTextShowsInfiniteLoopWhenNoRoundCapIsSet() {
        let result = ActiveTimerScreen.loopBadgeText(enabled: true, repeatRounds: 0, roundCount: 3)
        XCTAssertEqual(result, "Infinite Loop")
    }

    func testLoopBadgeTextShowsFiniteRoundProgress() {
        let result = ActiveTimerScreen.loopBadgeText(enabled: true, repeatRounds: 5, roundCount: 2)
        XCTAssertEqual(result, "Loop On · Round 2/5")
    }

    func testLoopBadgeTextClampsVisibleRoundToConfiguredLimit() {
        let result = ActiveTimerScreen.loopBadgeText(enabled: true, repeatRounds: 3, roundCount: 8)
        XCTAssertEqual(result, "Loop On · Round 3/3")
    }
}
