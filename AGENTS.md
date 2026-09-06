# AGENTS.md — Random Timer

## Interaction Language

All AI replies, code comments, commit messages, and documentation use **English**.

## Developer hub (start here for build/ship)

Unified journey + capability catalog: [`docs/DEVELOPERS.md`](docs/DEVELOPERS.md) and [`docs/developer_capabilities.json`](docs/developer_capabilities.json). Prefer that hub over scavenging overlapping guides. Audit with `python3 scripts/developers_docs_audit.py --repo-root .`.

## Communication Style

**Default to concise, action-first replies.** This is a standing rule.

1. **Keep routine replies short.** Prefer `1-3` bullets or a short paragraph.
2. **Lead with the action being taken.** Example: "I am patching `AGENTS.md` now."
3. **Do not give long explanations unless explicitly requested.**
4. **When the CEO asks for action steps, respond with action steps only.**
5. **If a deeper explanation is necessary, keep it brief and evidence-based.**

## Operational reliability contract

**Canonical doc:** `docs/OPERATIONAL_RELIABILITY.md` (evidence protocol, proxy vs ground truth, contradiction handling, metric semantics).

**Cursor:** `.cursor/rules/operational-reliability.mdc` (always applied).

Store and executive JSON expose **`review_count_metric_id`** where applicable so counts are never read as undefined “total reviews.”

## PR management & secrets (cross-reference)

Autonomous PR/branch hygiene and **never committing PATs** are defined in `CLAUDE.md` (including rotating leaked tokens, verifying `gh pr checks` before merge, resolving automated review threads that gate CI, and completion criteria for **"Done merging PRs"**). Do not embed CEO credentials in repo docs. External RAG/memory: use only when verified configured in-session.

**CTO session start (PR hygiene):** follow `CLAUDE.md` → *PR Management & System Hygiene* → *CTO session start protocol* (`gh auth status`, `git fetch --prune`, open PR audit, orphan branch map, merge only on green required checks, post-merge CI on `develop`/`main`). Say **"Done merging PRs"** only with merge SHAs and verified CI — never after a PAT appears in chat (rotate the token first; do not record it in docs).

**Completion phrase:** use **"Done merging PRs. CI passing. System hygiene complete. Ready for next session."** only after all open PRs are reviewed/merged or blocked with evidence, orphan branches/worktrees are addressed with before/after counts, stale files/logs are cleaned with counts, `develop` and `main` CI are verified by link, an operational dry run completes, and RAG/lesson logging status is read back. Never include secrets or PAT values in these docs or status reports.

**Stack Overflow:** Draft answers as Markdown under `marketing/referral_content/stackoverflow_answers/` (see `docs/STACK_OVERFLOW_PLAYBOOK.md`); include `develop` permalinks to this repo where we actually use the pattern, plus disclosure when linking our code.

## Agent-Model Matching Standard

To maximize system performance and cost-efficiency, all agents must adhere to the **Agent-Model Matching** standard defined in `.claude/rules/agent-model-matching.md`.

Gemini-specific operating directives are maintained in `docs/GEMINI.md` (canonical path enforced by repo hygiene checks).

- **Orchestration**: latest high-reasoning `Claude Sonnet` class model (UltraBrain) for planning and coordination.
- **Deep Specialist**: latest `Claude Opus` class model or strongest available `GPT-4o/5` class model (Deep) for complex refactoring.
- **Utility Runner**: latest fast, low-cost `Gemini Flash` or `Claude Haiku` class model (Quick) for search, analysis, and scaffolding.
- **UI/UX Specialist**: strongest multimodal `Gemini Pro` class model (Visual) for layout and visual QA tasks.

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
6. **Truthfulness is mandatory.** Never guess, never bluff, and never claim a state that is not directly verified. Every status claim must include reproducible proof (command/query used + sanitized output).

## Operator Mandate: Env + Secrets Verification Before Blockers

When a task depends on credentials, the agent must verify local and CI credential wiring before reporting any blocker.

1. **Always check `.env` key names first** (without exposing secret values).
2. **Always check GitHub Actions secret names second** (`gh secret list`) and confirm required names exist.
3. **If a key is provided by the user, update both `.env` and GitHub secrets immediately** when requested.
4. **Prove access with a real authenticated read/write test** (status code + endpoint + sanitized response).
5. **Never claim “no access” or ask the user to re-provide credentials** until steps 1–4 are completed and reported with evidence.

## Growth North Star (Effective February 23, 2026)

### Business Goal

**Earn $100/day after-tax from app sales** while improving product quality and operational reliability.

### Operating Budget Mandate (Effective March 2, 2026)

**Hard budget cap: `$20 USD/month` total external spend** across tooling, cloud services, ads, SaaS, and automation.

Enforcement rules:
- Prefer zero-cost approaches first (existing CI minutes, local tooling, OSS, existing subscriptions).
- Do not start any new paid service, campaign, or add-on that can exceed the monthly cap.
- If a required action cannot be completed within the cap, stop and request explicit CEO approval with the exact dollar amount and justification.
- Every spend-related status update must include current month-to-date spend estimate and remaining budget.

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
- `timer_completed` last 7d: `3` events by `2` users.
- `open_to_completed_rate` (30d): `24.24%` (32/132).
- Paid attribution last 30d: `0` distinct users, `0` campaign rows.
- Downloads (30d): iOS `9`, Android `0`, combined `9`.
- Apple Ads live serving evidence: API reports `1` campaign (`ENABLED`/`RUNNING`) with `0` taps and `$0.00` spend in the trailing 30 days.

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

## Android Agent Acceleration

- **Google Play:** default `android_track=production` in `native-release.yml`; never open testing unless CEO explicitly requests — see `docs/PLAY_TESTING_TRACKS.md`.
- Before Android platform/build/store-policy work, run `python3 scripts/android_agent_doctor.py --json` and use `docs/ANDROID_AGENT_WORKFLOW.md`.
- If Android CLI is installed, run `android update`, use `android docs search '<topic>'` for current official guidance, and use `android skills` for AGP, R8, edge-to-edge, Navigation, Compose, emulator, and release-build work.
- Do not make preview Android CLI tooling a hard CI dependency; CI remains Gradle wrapper, repo scripts, store API read-back, and explicit evidence.

## Worktree & Branch Protocol

### Mandatory for ALL Agents
1. **Use `isolation: "worktree"` for any code modification.** No exceptions.
2. **Never commit directly to `develop`, `main`, or the user's active branch.**
3. Push worktree branch to origin, then create a PR for review/merge.
4. After work is pushed, the worktree is cleaned up automatically on next session start.

### Multi-Agent Safety
- Other agents (Claude, Gemini, GPT, Cursor) may have active worktrees concurrently.
- The auto-cleanup hook (`.claude/hooks/worktree-cleanup.sh`) checks for:
  - Registered git worktrees (skipped — another agent is working)
  - `.git` link files (skipped — still connected)
  - Lock files (skipped — in use)
  - Dirty working trees (skipped — uncommitted changes)
- Only truly orphaned directories (no git link, no lock, no changes) are removed.

### Branch Naming
- Features: `feat/{description}`
- Fixes: `fix/{description}`
- Releases: `release/vX.Y.Z` (only branch type allowed to merge to `main`)
- Hotfixes: `hotfix/vX.Y.Z` (branches from `main`, merges to both `main` and `develop`)
- Agent worktrees: `worktree-agent-{id}` (auto-generated, ephemeral)

### Release Flow
1. `develop` → `release/vX.Y.Z` → TestFlight + Google Play → tag on `main` → merge back to `develop`
2. Hotfix: `main` → `hotfix/vX.Y.Z` → stores → tag on `main` → merge to `develop`

## Internal Distribution Approval

- **CEO sign-off is mandatory before TestFlight internal distribution starts.**
- **CEO sign-off is mandatory before Firebase internal distribution starts.**
- GitHub Actions environments enforce this via `testflight-signoff` and `firebase-signoff`.
- Do not claim an internal iOS/Firebase build is queued or running until the environment approval is granted.

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
