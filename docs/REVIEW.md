# Code Review Guidelines

## Always check

### Cross-Platform Parity (CRITICAL)
- Paywall UI must show identical tiers, pricing, and features on iOS and Android
- Any `isPro` / entitlement check must use the same logic on both platforms
- Debug backdoor behavior must match: same gesture, same duration, same result
- Timer range limits, gap constants, and defaults must match across platforms
- Voice callout milestones and cue text must match across platforms

### Billing & Entitlements
- Debug/backdoor entitlement overrides MUST persist through billing restore and transaction listeners
- `unlockProForDebug()` must set the highest entitlement level (`.elite` / `ELITE`), never `.base` or `.none`
- Any function that sets `entitlementLevel` must check `debugOverrideActive` first
- Subscription product IDs must be consistent between paywall UI and billing manager
- Fallback prices in UI must match actual store pricing

### Resource References
- Android `R.raw.*`, `R.drawable.*` references must have corresponding files in `res/`
- iOS asset catalog references must have corresponding assets
- Never reference resources that don't exist — this breaks compilation

### Python Scripts
- Never put `sys.exit()` at module top level — guard with `if __name__ == "__main__":`
- All functions imported by test files must actually exist in the source module
- CI scripts must not crash the test runner on import

### CI/CD
- Workflow job names must be unique — duplicate names cause status check confusion
- Artifact upload steps with `if-no-files-found: error` must only run when the generating step succeeded
- Version codes must be bumped before any Play Store upload
- Environment deployment branch policies must include the branch being deployed

## Style
- Kotlin: conventional commits, no default exports
- Swift: SwiftLint compliance, no force unwrapping in production code
- Both: named parameters for functions with 3+ arguments

## Skip
- Generated files under `native-android/app/build/`
- Generated files under `native-ios/build/`
- Fastlane metadata text files (store listing content)
- Marketing site files under `marketing/site/`
- Files under `.claude/` (agent configuration)
