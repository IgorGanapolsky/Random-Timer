# Apple Private Cloud Compute (lite) — free Foundation Models under SBP

Operating brief from [Apple Developer — Accessing Private Cloud Compute](https://developer.apple.com/private-cloud-compute/):

> Developers in the **App Store Small Business Program** with **fewer than 2 million first-time App Store downloads** can use Apple Foundation Models on **Private Cloud Compute (PCC)** with **no cloud API cost**, once the Private Cloud Compute entitlement is assigned.

## Why this is high ROI here

Random Timer’s hard monthly external spend cap is **$20**. Paid cloud LLM APIs for post-session coaching tips would burn budget with low leverage. PCC (when eligible) + on-device Foundation Models are **$0 cloud API** paths that still push the product North Star (**WQTU**: ≥3 `timer_completed` in trailing 7d).

## Eligibility (must stay true)

| Requirement | Source of truth |
|-------------|-----------------|
| App Store Small Business Program enrolled | Apple Developer / App Store Connect |
| First-time App Store downloads **&lt; 2M** across apps | Analytics in App Store Connect (not PostHog install proxies) |
| Entitlement `com.apple.developer.private-cloud-compute` assigned | Developer account → Get the entitlement |

If downloads later exceed 2M or SBP ends, Apple notifies and we must migrate within **6 months**.

**Proxy vs truth:** `marketing/data/store_downloads.json` PostHog `downloads_30d` is an install **proxy**, not App Store first-time download totals. Use it only as a coarse “nowhere near 2M” check.

## Runtime routing (product)

Prefer backends in order:

1. **Private Cloud Compute** — when the PCC language-model API is present in the SDK **and** runtime reports available (iOS 27+ expected; **not** in Xcode 26.5 / iOS 26.5 SDK).
2. **On-device** `SystemLanguageModel` / `LanguageModelSession` (iOS 26+) — free, private.
3. **Static fallback** tip strings — always available; never block session completion.

Implementation:

- `native-ios/RandomTimer/Sources/Services/AppleIntelligenceCoach.swift` — prompt + routing + sanitize (unit-tested)
- `native-ios/RandomTimer/Sources/Services/AppleIntelligenceCoachService.swift` — generate + store tip
- Entitlement declared in `native-ios/RandomTimer/RandomTimer.entitlements`
- Post-session hook in `TimerManager.recordTrainingSessionCompleted`
- Tip surfaced on `TimerSetupScreen` via `@AppStorage("apple_intelligence_last_tip")`

## Anti-pattern

**Claiming paid cloud AI or live PCC when we are still eligible for zero-cost Apple Intelligence** — or claiming “PCC is live in production” before the SDK exposes `PrivateCloudComputeLanguageModel` and the entitlement is assigned on the Apple account.

## Health signals (required)

| Signal | Meaning here |
|--------|----------------|
| `sbp_download_cap_tracked` | Track SBP + &lt;2M first-time downloads; never invent totals |
| `entitlement_declared_in_repo` | `com.apple.developer.private-cloud-compute` in app entitlements |
| `prefer_pcc_then_on_device_then_static` | Routing prefers PCC → on-device → static |
| `zero_cloud_api_cost_under_cap` | No paid LLM SaaS for this tip path under the hard cap |
| `no_claim_pcc_runtime_without_sdk` | Do not claim PCC runtime until SDK + entitlement evidence exists |

## Fitness

```bash
python3 scripts/apple_pcc_gate.py --json
```

## Explicitly rejected

- Paying OpenAI/Anthropic/etc. for short post-session coaching tips while SBP + &lt;2M eligibility holds
- Claiming App Store first-time downloads from PostHog install proxies
- Claiming PCC production traffic on Xcode 26.5 (API absent)
- Skipping static fallback so session completion depends on model availability
