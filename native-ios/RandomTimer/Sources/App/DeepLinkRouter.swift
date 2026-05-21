import Foundation
import Observation

struct PaywallDeepLinkRequest: Equatable, Identifiable {
    let id: UUID
    let entryPoint: PaywallEntryPoint
}

@Observable
@MainActor
final class DeepLinkRouter {
    private(set) var paywallRequest: PaywallDeepLinkRequest?

    func handle(_ url: URL) {
        guard let entryPoint = Self.paywallEntryPoint(from: url) else { return }
        paywallRequest = PaywallDeepLinkRequest(id: UUID(), entryPoint: entryPoint)
    }

    nonisolated static func paywallEntryPoint(from url: URL) -> PaywallEntryPoint? {
        guard isSupported(url: url), isUpgradeIntent(url: url) else { return nil }
        let query = URLComponents(url: url, resolvingAgainstBaseURL: false)?
            .queryItems?
            .reduce(into: [String: String]()) { result, item in
                result[item.name] = item.value
            } ?? [:]
        let requested = query["entry_point"] ?? query["feature"] ?? "setup_upgrade_cta"
        return normalizedPaywallEntryPoint(requested)
    }

    nonisolated static func normalizedPaywallEntryPoint(_ value: String) -> PaywallEntryPoint {
        if let entryPoint = PaywallEntryPoint(rawValue: value) {
            return entryPoint == .unknown ? .setupUpgradeCTA : entryPoint
        }
        switch value {
        case "extended_range": return .rangeGate
        case "voice_callouts": return .voiceGate
        case "repeat_loop": return .repeatGate
        case "pro_sounds": return .soundArsenalGate
        default: return .setupUpgradeCTA
        }
    }

    private nonisolated static func isSupported(url: URL) -> Bool {
        if url.scheme == "randomtimer", url.host == "open" {
            return true
        }
        return (url.scheme == "https" || url.scheme == "http")
            && url.host == "igorganapolsky.github.io"
            && url.path.hasPrefix("/Random-Timer")
    }

    private nonisolated static func isUpgradeIntent(url: URL) -> Bool {
        let pathParts = url.path
            .split(separator: "/")
            .map { String($0).lowercased() }
        let query = URLComponents(url: url, resolvingAgainstBaseURL: false)?
            .queryItems?
            .reduce(into: [String: String]()) { result, item in
                result[item.name] = item.value?.lowercased()
            } ?? [:]
        return pathParts.contains("upgrade")
            || pathParts.contains("paywall")
            || pathParts.contains("pro")
            || ["upgrade", "paywall", "pro"].contains(query["screen"])
            || ["upgrade", "paywall", "pro"].contains(query["route"])
            || ["upgrade", "paywall", "pro"].contains(query["target"])
    }
}
