# Autonomous Operations (24/7 + GSD)

How Random Timer runs continuously without CEO action on every step, and where human gates remain.

**Budget:** Hard cap **$20/month** external spend (`CLAUDE.md`). Scheduled jobs use GitHub Actions minutes, PostHog/ASC/Play APIs already in use — no new paid services without CEO approval.

**Actions:** This repo is **public** — standard hosted runner minutes are **free**. Org caps and **Anthropic** (`claude-review`) still matter. See `docs/ACTIONS_BUDGET.md`.

**GSD (Get Shit Done):** Each automation cycle must end with a concrete artifact: merge SHA, workflow run URL, committed JSON snapshot, or wiki update — not a plan.

**Ralph Loop:** Multi-step implement → test → fix cycles for code tasks. See `.claude/skills/ralph-mode.md` and `.claude/scripts/ralph-loop.sh`.

```bash
.claude/scripts/ralph-loop.sh start "<task>" ISSUE-123
.claude/scripts/ralph-loop.sh check    # pytest scripts/tests + Android unit tests
.claude/scripts/ralph-loop.sh loop     # retry until green
.claude/scripts/ralph-loop.sh stop
```

Ralph state: `.claude/ralph/ATTEMPTS.md` (session-local; not committed).

---

## What runs 24/7 automatically (no CEO click)

| Schedule | Workflow | Purpose |
|----------|----------|---------|
| Every 6 h (:05 UTC) | `wiki-sync.yml` | PostHog → `marketing/data/*.json`, commit to `develop`, publish GitHub Wiki |
| Daily 06:17 UTC | `executive-metrics.yml` | `executive_metrics.json` artifact (WQTU, paywall, stores) |
| Daily 14:10 UTC | `north-star-guardrail.yml` | WQTU guardrail snapshot |
| Daily 13:15 UTC | `daily-growth-publishing.yml` | Blog / Pages growth pipeline |
| Every 6 h | `main.yml` | Legacy metrics cadence |
| Every 6 h ( :25 ) | `zernio-growth-orchestration.yml` | Growth orchestration |
| Every 30 min | `store-release-watcher.yml`, `resolve-bot-comments.yml` | Release + bot hygiene |
| Weekly (calendar) | `analytics.yml`, `weekly-*`, `wqtu-health.yml` | ASO, CRO, referrals, attribution |
| On push `develop`/`main` | `internal-distribution.yml` | **Starts** internal builds (see gates below) |
| On PR/push | `ci.yml` | Unit tests, lint, **`app-debug` APK** artifact |

Machine-readable registry: `.claude/scheduled_tasks.json` (documentation mirror of cron workflows).

---

## CEO gates (cannot be automated)

| Gate | Environment / location | Unblocks |
|------|-------------------------|----------|
| Firebase internal APK | `firebase-signoff` | `android-firebase-internal` in `internal-distribution.yml` |
| TestFlight internal | `testflight-signoff` | `ios-testflight-internal` |
| Production store upload | `production-signoff` | `native-release.yml` upload jobs |
| Play public version | Play Console → **Publish changes** | Managed publishing — approved builds stay staged until published |
| Play IAP catalog | Play Console → Monetize → Products | `pro_base`, `elite_tactical`, `elite_tactical_monthly` must exist and be active |
| App Store review | ASC | Optional `submit_review` on release workflow |

Commit statuses required before production (`scripts/internal_signoff_gate.py`):

- Android: `internal-signoff/firebase`
- iOS: `internal-signoff/testflight`

---

## Standard operator flows (automate up to the gate)

### Internal Android build (Firebase)

```bash
gh workflow run internal-distribution.yml --ref develop -f target=android_firebase
```

Then CEO: GitHub → Actions run → **Review deployments** → approve **`firebase-signoff`**.

Evidence: job log `uploaded new release` / `distributed to testers/groups successfully`; console project **`random-timer-dist-new`** (`docs/FIREBASE_ANDROID_INFRASTRUCTURE.md`).

### Internal full stack (TestFlight + Play internal + Firebase)

```bash
gh workflow run internal-distribution.yml --ref develop -f target=all
```

Approve **`testflight-signoff`** and **`firebase-signoff`** when prompted.

### Production release (after internal signoffs on exact SHA)

```bash
gh workflow run native-release.yml --ref release/vX.Y.Z -f platform=both -f android_track=production
```

Approve **`production-signoff`**.

**Shipped = API verify + GitHub tag.** `native-release.yml` produces a GitHub release and verifies the build landed on the correct Play track and TestFlight slot. That is the release proof.

**Publicly visible ≠ shipped.** `public-store-version-readback.yml` checks iTunes lookup and Play HTML — both are lagging proxies (hours to 24h+). Do **not** re-trigger the release pipeline because that workflow fails. Use `store-release-watcher.yml` (cron `*/30 * * * *`) or trigger `public-store-version-readback.yml` manually later.

See `.claude/skills/store-verify-ci.md` for the full tiered truth model and debug runbook.

### Ralph / agent code change

1. Worktree branch (`feat/*` / `fix/*` off `develop`) — `CLAUDE.md`
2. Ralph loop or TDD per `AGENTS.md`
3. PR → green `ci.yml` → merge
4. `develop` CI produces `app-debug` artifact

---

## Push-triggered internal distribution

On every push to `develop` or `main`, `internal-distribution.yml` runs with `target=all` but **waits** on signoff environments until CEO approves. Recent pushes may show `waiting` on `Android Firebase Signoff` — that is expected, not a failure.

Use `target=all_safe` to skip Firebase when debugging Play internal only.

---

## Evidence protocol

All status claims: command + path + sanitized output (`docs/OPERATIONAL_RELIABILITY.md`). Agents must not claim Firebase email, store version, or revenue without workflow log or API read-back.

---

## Claude Code local auth

For interactive Claude Code (not CI), use **`apiKeyHelper`** so keys never land in repo or chat. See **`docs/CLAUDE_CODE_API_KEY_HELPER.md`** and copy **`.claude/scripts/get-anthropic-api-key.sh.example`** to `~/.claude/get-anthropic-api-key.sh`.

## Related docs

- `docs/CLAUDE_CODE_API_KEY_HELPER.md` — Claude Code `apiKeyHelper` + TTL
- `docs/RELEASE.md` — version bump, release branches, store metadata paths
- `docs/FIREBASE_ANDROID_INFRASTRUCTURE.md` — Firebase project split, tester emails
- `docs/PLAY_CONSOLE_IAP_RUNBOOK.md` — IAP SKU checklist (console-only P0)
- `docs/workflow.md` — proof-of-work for agent PRs
- `wiki/Growth-Systems-Overview.md` — weekly growth calendar
