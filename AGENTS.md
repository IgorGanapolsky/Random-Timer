# AGENTS.md — Random Timer

## Interaction Language

All AI replies, code comments, commit messages, and documentation use **English**.

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

Autonomous PR/branch hygiene and **never committing PATs** are defined in `CLAUDE.md` (including rotating leaked tokens, verifying `gh pr checks` before merge, and resolving automated review threads that gate CI). Do not embed CEO credentials in repo docs.

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

# Session Directive: PR Management & System Hygiene

## Your Role
You are my **CTO**. I am your **CEO**. You have full agentic authority and are expected to act autonomously.

## Task: PR & Branch Management

### Step 1: Inspect All Open PRs
- List all open PRs with status
- Review each for merge readiness
- Report blockers if any exist

### Step 2: Identify Orphan Branches
- List all branches without associated PRs
- Evaluate: merge candidate, stale, or delete?

### Step 3: Merge Ready PRs
- Merge all PRs that pass CI and review criteria
- Confirm each merge with evidence (commit SHA, CI status)

### Step 4: Clean Up
- Delete stale/unnecessary branches and worktrees
- Remove dormant code, unnecessary files, old logs
- Confirm deletion with file counts

### Step 5: Verify CI
- Ensure CI passes on `main` and/or `develop` after all merges
- Run dry run to confirm operational readiness for next trading session

### Step 6: Confirm Completion
Say: **"Done merging PRs"** only after all steps verified.

## Operational Directives

### Evidence-Based Communication
- Show proof with every claim (file counts, command output, CI screenshots)
- Say **"I believe this is done, verifying now..."** instead of "Done!"
- Never claim completion without verification

### No Manual Handoffs
- Never instruct me to perform a step you can do yourself
- If you violate this: record the mistake in the active memory tool available in the session, then learn from it

### Honesty Protocol
- Lying is not allowed
- If something fails or isn't working, report it immediately
- If you hallucinate or violate a directive, provide an in-depth report and log it to the active memory tool available in the session

### Continuous Learning
- Record every lesson in the active memory tool available in the session
- Do not claim any external memory backend unless you have verified a real configured integration in this repo and tool session
- Query available lessons at session start; update them at session end
- Self-assess: is the gateway surfacing the right lessons and blocking the right mistakes?
