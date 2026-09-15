import Foundation
import os

#if canImport(FoundationModels)
import FoundationModels
#endif

/// Generates short post-session coaching tips via Apple Foundation Models.
///
/// - On-device: `SystemLanguageModel` (iOS 26+) — free, private.
/// - Private Cloud Compute: entitlement-ready; `PrivateCloudComputeLanguageModel`
///   ships with iOS 27 SDK (not in Xcode 26.5). Prefer PCC when the runtime
///   reports it available; until then we stay on-device / static fallback.
/// - Eligibility for zero-cost PCC: App Store Small Business Program +
///   <2M first-time downloads + `com.apple.developer.private-cloud-compute`.
@MainActor
final class AppleIntelligenceCoachService {
    static let shared = AppleIntelligenceCoachService()

    private let defaults = UserDefaults.standard
    private let tipKey = "apple_intelligence_last_tip"
    private let backendKey = "apple_intelligence_last_backend"
    private let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "AppleIntelligenceCoach")

    private init() {}

    var lastTip: AppleIntelligenceCoach.Tip? {
        guard let text = defaults.string(forKey: tipKey), !text.isEmpty else { return nil }
        let backend = AppleIntelligenceCoach.Backend(rawValue: defaults.string(forKey: backendKey) ?? "")
            ?? .staticFallback
        return AppleIntelligenceCoach.Tip(text: text, backend: backend)
    }

    func refreshTipAfterSession(lastDurationSeconds: Int?) {
        let context = AppleIntelligenceCoach.SessionContext(
            totalSessions: TrainingStatsService.shared.totalSessions,
            currentStreak: TrainingStatsService.shared.currentStreak,
            lastDurationSeconds: lastDurationSeconds
        )
        Task { await self.generateAndStore(context: context) }
    }

    func generateAndStore(context: AppleIntelligenceCoach.SessionContext) async {
        let tip = await generateTip(context: context)
        defaults.set(tip.text, forKey: tipKey)
        defaults.set(tip.backend.rawValue, forKey: backendKey)
        log.info("Stored coaching tip via \(tip.backend.rawValue, privacy: .public)")
    }

    func generateTip(context: AppleIntelligenceCoach.SessionContext) async -> AppleIntelligenceCoach.Tip {
        let onDevice = isOnDeviceModelAvailable()
        // PCC type is not in the iOS 26.5 SDK; keep the routing hook for iOS 27+.
        let pcc = false
        let backend = AppleIntelligenceCoach.preferredBackend(
            pccRuntimeAvailable: pcc,
            onDeviceRuntimeAvailable: onDevice
        )

        switch backend {
        case .privateCloudCompute, .onDevice:
            if let generated = await generateWithFoundationModels(context: context) {
                return AppleIntelligenceCoach.Tip(text: generated, backend: .onDevice)
            }
            return AppleIntelligenceCoach.fallbackTip(for: context)
        case .staticFallback:
            return AppleIntelligenceCoach.fallbackTip(for: context)
        }
    }

    private func isOnDeviceModelAvailable() -> Bool {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, *) {
            return SystemLanguageModel.default.isAvailable
        }
        #endif
        return false
    }

    private func generateWithFoundationModels(
        context: AppleIntelligenceCoach.SessionContext
    ) async -> String? {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, *) {
            let model = SystemLanguageModel.default
            guard model.isAvailable else { return nil }
            do {
                let session = LanguageModelSession(
                    model: model,
                    instructions: AppleIntelligenceCoach.instructions
                )
                let response = try await session.respond(
                    to: AppleIntelligenceCoach.prompt(for: context)
                )
                return AppleIntelligenceCoach.sanitizeModelOutput(response.content)
            } catch {
                log.error("FoundationModels respond failed: \(error.localizedDescription, privacy: .public)")
                return nil
            }
        }
        #endif
        return nil
    }
}
