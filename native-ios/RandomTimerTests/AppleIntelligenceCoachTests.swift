import XCTest
@testable import RandomTimer

final class AppleIntelligenceCoachTests: XCTestCase {
    func testPreferredBackendPrefersPCCThenOnDevice() {
        XCTAssertEqual(
            AppleIntelligenceCoach.preferredBackend(
                pccRuntimeAvailable: true,
                onDeviceRuntimeAvailable: true
            ),
            .privateCloudCompute
        )
        XCTAssertEqual(
            AppleIntelligenceCoach.preferredBackend(
                pccRuntimeAvailable: false,
                onDeviceRuntimeAvailable: true
            ),
            .onDevice
        )
        XCTAssertEqual(
            AppleIntelligenceCoach.preferredBackend(
                pccRuntimeAvailable: false,
                onDeviceRuntimeAvailable: false
            ),
            .staticFallback
        )
    }

    func testPromptIncludesSessionStats() {
        let prompt = AppleIntelligenceCoach.prompt(
            for: .init(totalSessions: 4, currentStreak: 2, lastDurationSeconds: 90)
        )
        XCTAssertTrue(prompt.contains("4"))
        XCTAssertTrue(prompt.contains("2"))
        XCTAssertTrue(prompt.contains("90"))
    }

    func testSanitizeTrimsQuotesAndCapsLength() {
        let long = (0..<40).map { "word\($0)" }.joined(separator: " ")
        let sanitized = AppleIntelligenceCoach.sanitizeModelOutput("\"\(long)\"")
        XCTAssertFalse(sanitized.contains("\""))
        XCTAssertLessThanOrEqual(sanitized.split(separator: " ").count, 18)
    }

    func testFallbackEncouragesQualifiedTraining() {
        let tip = AppleIntelligenceCoach.fallbackTip(
            for: .init(totalSessions: 0, currentStreak: 0, lastDurationSeconds: nil)
        )
        XCTAssertEqual(tip.backend, .staticFallback)
        XCTAssertTrue(tip.text.lowercased().contains("three") || tip.text.lowercased().contains("rep"))
    }
}
