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

## Operator Mandate: Env + Secrets Verification Before Blockers

When a task depends on credentials, the agent must verify local and CI credential wiring before reporting any blocker.

1. **Always check `.env` key names first** (without exposing secret values).
2. **Always check GitHub Actions secret names second** (`gh secret list`) and confirm required names exist.
3. **If a key is provided by the user, update both `.env` and GitHub secrets immediately** when requested.
4. **Prove access with a real authenticated read/write test** (status code + endpoint + sanitized response).
5. **Never claim “no access” or ask the user to re-provide credentials** until steps 1–4 are completed and reported with evidence.

## Growth North Star (Effective February 23, 2026)

### Primary North Star Metric (NSM)

**Weekly Qualified Training Users (WQTU)**: number of distinct users with **3 or more `timer_completed` events** in the trailing 7 days.

This is the product-value metric for Random Tactical Timer (repeat stress/reaction training), not a vanity install metric.

### Canonical Query (PostHog HogQL)

```sql
SELECT count(*)
FROM (
  SELECT person_id
  FROM events
  WHERE event = 'timer_completed'
    AND timestamp > now() - interval 7 day
  GROUP BY person_id
  HAVING count() >= 3
)
```

### Guardrails (must be tracked with NSM)

1. **Paid efficiency**: blended paid CPI <= `$3.00` (target), with Apple Ads benchmark context checked monthly.
2. **Activation quality**: `open_to_completed_rate` >= `25%`.
3. **Retention floor**: D30 retention >= `6%` (target above broad-market baselines).
4. **Attribution hygiene**: `paid_distinct_users_30d` and campaign-level UTM rows must be non-empty before claiming paid impact.

### Baseline Snapshot (2026-02-24 UTC)

- `WQTU`: `0` (no user reached >=3 `timer_completed` in trailing 7d).
- `timer_completed` last 7d: `2` events by `1` user.
- `open_to_completed_rate` (30d): `24.24%` (32/132).
- Paid attribution last 30d: `0` distinct users, `0` campaign rows.
- Downloads (30d): iOS `8`, Android `0`, combined `8`.
- Apple Ads live serving evidence: account shows `0` campaigns and `0` spend rows in dashboard (`Last 7 days` view).

### Targets

- **Checkpoint target (2026-03-31):** `WQTU >= 8`
- **Quarter target (2026-06-30):** `WQTU >= 25`

### Execution Rule

When asked “are we on track to our North Star?”, answer only from:

- live PostHog query results,
- latest campaign serving + spend evidence,
- and current WQTU versus target.

Do not infer progress from draft campaign configs.

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
