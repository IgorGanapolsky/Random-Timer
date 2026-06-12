# CI/CD gap: Random Timer vs AgentLeash

**Date:** 2026-06-03  
**Scope:** Publishing and GitHub Actions ship path only (no workflow changes in the doc PR).  
**Companion:** Device/E2E parity vs 2026 practice → [`CI_CD_GAP_ANALYSIS_2026-05-26.md`](CI_CD_GAP_ANALYSIS_2026-05-26.md).

## Executive summary

**AgentLeash** ships as a **single consolidated Android trunk pipeline** ([`mobile.yml`](https://github.com/IgorGanapolsky/AgentLeash/blob/develop/.github/workflows/mobile.yml)): push to `develop` → test, debug APK, release AAB → Play **internal** (and Firebase on `develop`); optional **production promote** (10% rollout) without GitHub Environment signoffs or `release/v*` branch cuts. Version code is **`git rev-list --count HEAD`** in CI.

**Random Timer** is **production-hardened but operationally heavy**: dual platform (iOS + Android), **three CEO signoff environments**, **SHA-locked internal proof** before production upload, and a **`release/v*` → `main`** release train. That is intentional reliability debt from real incidents (signoff races, store truth lag, ASC complexity)—not neglect. Operational detail lives in [`AUTONOMOUS_OPERATIONS.md`](AUTONOMOUS_OPERATIONS.md), [`RELEASE.md`](RELEASE.md), and schedule policy in [`ACTIONS_BUDGET.md`](ACTIONS_BUDGET.md).

**Note:** AgentLeash “modernization” is narrower scope (Android-only, pre-revenue). A fast pipeline does not imply proven production; RTT’s gates exist because shipping scope is wider.

---

## Comparison table

| Capability | AgentLeash | Random Timer | Gap impact |
|------------|------------|--------------|------------|
| **Workflow count** | 6 | 74 | RTT: queue noise, hard to reason about ship path; AL: one mental model |
| **Consolidated mobile CI** | Single [`mobile.yml`](https://github.com/IgorGanapolsky/AgentLeash/blob/develop/.github/workflows/mobile.yml): test + debug APK + release AAB | Split: `ci.yml`, `device-tests.yml`, many store workflows | RTT: longer PR cycles, macOS device cost |
| **Trunk publish (push `develop`)** | Play internal + Firebase on `develop`; promote on `develop` push | `internal-distribution.yml` starts on push but **blocks** on signoff envs; production = **dispatch only** | RTT: CEO steps per ship; AL: hands-off after secrets |
| **Branch model** | `develop` default; `main` release-only | `develop` trunk + **`release/v*`** → `main` + hotfix | RTT: manual branch cut, version notes, PR to main |
| **Version bump** | CI overwrites `versionCode` from commit count | `bump-version.sh` + changelogs + cross-platform semver | RTT: friction; fewer “wrong code” risks |
| **CEO signoff gates** | None | Firebase, TestFlight, production environments | RTT: safe; AL: fast but no human gate on promote |
| **iOS / App Store** | N/A (Android-only) | TestFlight, match, metadata sync, submit-review, cert regen | RTT complexity is **real scope**, not CI sloppiness |
| **Fastlane** | Root `fastlane/`, promote lanes + metadata | `native-android/` + `native-ios/` fastlane, many locales | RTT: listing parity work AL never needed |
| **Automerge** | Not used | `autonomous-release-automerge.yml` for `release/*` → `main` only | RTT: automerge is **release-train**, not trunk |
| **Merge queue** | No | `merge_group` in `ci.yml` only | RTT: partial; not end-to-end ship queue |
| **Metadata sync** | `fastlane metadata` lane | `ios-metadata-sync`, `android-metadata-sync`, ASC scripts | RTT: stronger, more moving parts |
| **Monthly release** | No | `monthly-pro-content-release.yml` | RTT: product ops AL does not have |
| **Ops verification** | Optional Sonar; status digest | `operational-verification-bundle`, store watchers, executive metrics | RTT: evidence-heavy NSM/revenue ops |
| **Production promote** | `promote_internal_to_production` on develop push | `play-promote-to-production.yml` + `native-release` dispatch | RTT: staged, manual inputs where API cannot resolve latest internal |
| **Doc vs reality** | `PUBLISH.md` may cite older workflow names; ship path is `mobile.yml` | [`RELEASE.md`](RELEASE.md) matches signoff policy (2026) | AL: doc drift; RTT: docs match complexity |

---

## Why Random Timer lags (root causes)

1. **Dual store + IAP + managed publishing** — iOS ASC and Play production are not one-button. Internal proof on **exact SHA** was added after signoff/status races ([`RELEASE.md`](RELEASE.md), [`AUTONOMOUS_OPERATIONS.md`](AUTONOMOUS_OPERATIONS.md)).
2. **Firebase, TestFlight, and Play internal are three systems** — `internal-distribution.yml` and `internal_signoff_gate.py` exist because a single pipeline could not prove “CEO tested this binary.”
3. **Release train over trunk ship** — `release/v*` → `main`, `enforce-release-branch-to-main`, release notes manifest, and disabled auto-sync favor **auditability** over AgentLeash-style continuous promote.
4. **Growth/NSM automation sprawl** — daily/weekly workflows (WQTU, ASO, referrals, wiki-sync) accumulated for the revenue North Star; AgentLeash is Android-only and pre-revenue.
5. **AgentLeash is younger and narrower** — implementation chose a simpler LLC Android path (org account, no iOS) without CEO gates; RTT conventions are referenced in AgentLeash docs but not copied wholesale.

---

## Top 5 modernization moves (PR-sized, ≤ $20/mo)

Prioritized from repo comparison (2026-06-03). **No workflow edits in the doc-only PR**; each row is a follow-up PR.

| # | Move | Scope | Cost |
|---|------|--------|------|
| **1** | **Tier-0 ship contract** — Document and enforce exactly three paths: PR `ci` + `app-debug` artifact; push `internal-distribution`; dispatch `native-release`. Demote non-ship workflows to `workflow_dispatch` or Tier 2 schedules per [`ACTIONS_BUDGET.md`](ACTIONS_BUDGET.md). | Docs + one PR trimming `on:` / schedules | $0 |
| **2** | **Trunk Android internal (AgentLeash pattern)** — On green `develop` push: auto-upload Play **internal** AAB (reuse commit-count or existing bump script). **Keep** `firebase-signoff` and `production-signoff`; do **not** auto-promote production on `develop`. | `internal-distribution.yml` or slim post-job on `ci.yml` | $0 (public repo minutes) |
| **3** | **Collapse Play promote** — Single fastlane lane `promote_internal_to_production` (AgentLeash-style) from `native-release` instead of separate `play-promote-to-production` + manual `versionCode` where API can resolve latest internal. | Fastlane + `native-release.yml` | $0 |
| **4** | **iOS stays release-branch; Android hotfix trunk** — Allow `native-release` from `develop` for `platform=android` only after internal statuses on SHA; keep iOS on `release/v*`. | `release_intent_gate.py` + docs | $0 |
| **5** | **Merge queue for ship PRs** — Extend `merge_group` to required checks on `release/*` → `main` (or ruleset queue on `develop`) after Tier-0 stabilizes. | Branch protection / ruleset | $0 |

**Avoid:** paid merge-queue SaaS, new Sonar org, extra macOS device matrix—stay within existing Actions and CEO signoffs for production.

---

## Evidence anchors

| Claim | Where to verify |
|-------|-----------------|
| AgentLeash trunk ship | [`.github/workflows/mobile.yml`](https://github.com/IgorGanapolsky/AgentLeash/blob/develop/.github/workflows/mobile.yml) (`develop` → Firebase/internal; optional production promote) |
| RTT CEO gates and 24/7 ops | [`AUTONOMOUS_OPERATIONS.md`](AUTONOMOUS_OPERATIONS.md) |
| RTT release train and signoff policy | [`RELEASE.md`](RELEASE.md) |
| RTT schedule tiers and caps | [`ACTIONS_BUDGET.md`](ACTIONS_BUDGET.md) |
| RTT internal / production workflows | `.github/workflows/internal-distribution.yml`, `native-release.yml` |
| Scale (order of magnitude) | ~6 vs ~74 workflow files under `.github/workflows/` |

---

## Related links

- AgentLeash consolidated pipeline: [IgorGanapolsky/AgentLeash `mobile.yml`](https://github.com/IgorGanapolsky/AgentLeash/blob/develop/.github/workflows/mobile.yml)
- Random Timer autonomous ops: [`AUTONOMOUS_OPERATIONS.md`](AUTONOMOUS_OPERATIONS.md)
- Random Timer release process: [`RELEASE.md`](RELEASE.md)
- Random Timer Actions budget: [`ACTIONS_BUDGET.md`](ACTIONS_BUDGET.md)
