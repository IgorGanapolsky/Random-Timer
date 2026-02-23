# AGENTS.md — Random Timer

## Agent-Model Matching Standard

To maximize system performance and cost-efficiency, all agents must adhere to the **Agent-Model Matching** standard defined in `.claude/rules/agent-model-matching.md`.

- **Orchestration**: `claude-3-5-sonnet` (UltraBrain) for planning and coordination.
- **Deep Specialist**: `claude-3-opus` or `gpt-4o` (Deep) for complex refactoring.
- **Utility Runner**: `gemini-1.5-flash` or `claude-3-haiku` (Quick) for search, analysis, and scaffolding.
- **UI/UX Specialist**: `gemini-1.5-pro` (Visual) for multimodal and layout tasks.

When delegating work via the `Task` tool, agents should specify the category (e.g., `subagent_type: "Quick"`) to ensure the correct model is selected from the fallback chain.

## Mandate: Never Claim Readiness Without Verification

**This is the highest-priority rule. Violations are treated as critical failures.**

1. **Never say something is "done", "uploaded", "ready", or "complete" without reading back the actual state.** API objects existing (e.g., screenshot sets) does not mean they contain data. Always verify contents, not just existence.
2. **Never confuse metadata scaffolding with actual content.** An empty screenshot set is not "screenshots uploaded." A created app version is not "app submitted."
3. **When checking App Store Connect via API, always drill into child resources.** Screenshot sets → verify screenshot count inside each. Localizations → verify each required field has a non-empty value. Builds → verify processingState is VALID.
4. **Before claiming an App Store submission is ready, verify ALL of the following:**
   - Screenshots: at minimum 3 screenshots per required device class (6.9" or 6.5" iPhone AND 13" iPad)
   - Build: attached and processingState == VALID
   - Description: non-empty
   - Keywords: non-empty
   - Support URL: non-empty
   - Privacy Policy URL: set (if required)
   - Age Rating: completed
   - Category: set
   - Pricing: set (Free or paid)
   - App Review contact info: filled
5. **Show evidence, not assertions.** When reporting status, include actual counts, actual field values, actual HTTP responses — not summaries or assumptions.

## Act Like the World's Top iOS App Publisher

- Research before acting. Read Apple's current documentation, not cached assumptions.
- Generate real device screenshots at exact pixel dimensions Apple requires. Never upscale or stretch.
- Use `fastlane deliver` or the App Store Connect API correctly — verify every upload succeeded with a read-back.
- Treat every App Store rejection as a preventable failure. Anticipate review issues before submission.
- When something fails, diagnose the root cause from the actual error response before retrying.

## Commands

```bash
# Android
cd native-android && ./gradlew assembleDebug          # Build debug APK
cd native-android && ./gradlew testDebugUnitTest       # Run unit tests
cd native-android && ./gradlew lint                    # Lint check

# iOS
cd native-ios && xcodebuild -scheme RandomTimer build  # Build
cd native-ios && xcodebuild -scheme RandomTimer test   # Run tests
```
