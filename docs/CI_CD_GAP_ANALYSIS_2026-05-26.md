# CI/CD gap analysis — Random Timer vs 2026 mobile best practice

**Date:** 2026-05-26  
**Evidence:** GitHub Actions run history, workflow YAML, local device-test runs this session.

## Executive summary

**CI does not “suck” on merge rate** — recent `device-tests.yml` and `ci.yml` runs on `develop` are **success** (e.g. [device-tests #26463239153](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/26463239153), [ci #26462519393](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/26462519393)).

What **does** hurt us is **local ↔ CI parity**, **misleading job names**, **unenforced quality gates**, and **environment-specific toolchain traps** (Gradle JetBrains JVM pin, iOS 26 + Maestro discovery, Samsung multi-user `adb`).

Top teams in 2026 optimize for **deterministic environments**, **one runner contract**, **PR smoke + nightly depth**, and **measured flakiness** — not maximum job count.

---

## What top teams do in 2026 (synthesis)

Sources: [Getir — Maestro at scale (Mar 2026)](https://medium.com/getir/maestro-at-scale-architecting-a-deterministic-mobile-test-platform-0298b012f7a8), [Assrt — emulator CI without device farm](https://assrt.ai/t/mobile-app-ci-testing-without-device-farm), [Maestro docs](https://docs.maestro.dev/), industry flaky-E2E writeups (Apr 2026).

| Practice | What “good” looks like |
|----------|----------------------|
| **Runner contract** | One bash entrypoint per platform; same on laptop, GHA, and device farm |
| **Deterministic data** | Mock/stub backends or seeded fixtures — not shared staging |
| **Selectors** | `testID` / accessibility id first; text last |
| **PR gate** | Fast smoke (1 emulator + 1 simulator), &lt;15–20 min |
| **Depth** | Nightly: full Maestro suites, sharded, with artifacts |
| **Flake policy** | Quarantine + flake rate metric; rerun failed jobs, don’t ignore |
| **JDK alignment** | Same major JDK on CI and local (21 for AGP 9 / Gradle 9) |
| **Coverage** | Enforced threshold on changed code or aggregate with trend |

---

## What we have today (evidence)

### Workflows

| Workflow | Role | Cancel in-flight? | Typical duration |
|----------|------|-------------------|------------------|
| `ci.yml` | Lint, unit tests, APK, Codecov | **Yes** | ~5–15 min (path-aware) |
| `device-tests.yml` | Android emulator + iOS Maestro | **No** (correct for long iOS) | Android ~30m; iOS **15–50m** |
| `flaky-test-audit.yml` | Python 3× rerun weekly | Yes | 30m |

### Android device job — name vs reality

Job title: **“Android Emulator + Maestro Tests”**.

Actual script (`scripts/device-tests/ci-maestro.sh`):

- Runs **Compose** `TimerSetupSmokeTest` only — **not** `.maestro/*.yaml`.

Local `run-all.sh` runs **Maestro YAML** flows. That is a **parity gap**: green CI does not prove Maestro flows pass.

### iOS device job

- **macos-15**, builds app, runs **Maestro** + optional Agent Device (`ci-maestro-ios.sh`).
- **Local macOS 26.5**: Maestro often reports **0 devices**; **XCUITest** via `run-ios-xctest.sh` is the reliable local path (added 2026-05-26).

### Quality gates (`.github/ci-config.yml`)

| Gate | Documented | Enforced in CI? |
|------|------------|-----------------|
| `test_coverage` minimum **80%** | Yes | **No** — no `--cov-fail-under=80` in `ci.yml` |
| Sonar security A on new code | Yes | **Yes** — blocks some PRs (e.g. #1618) |
| Device tests on every PR | Partial | Path-aware — skipped if no native changes |

### Local-only failure modes (this session)

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Gradle “JetBrains 21” download failed | `gradle-daemon-jvm.properties` (gitignored, often generated locally) + no foojay URL on **macOS arm64** | Remove file; use `openjdk@21`; scripts disable pin during device tests |
| Maestro “Unable to locate Java Runtime” | macOS `/usr/bin/java` stub | `bootstrap-macos.sh` + `lib/common.sh` |
| `adb install` signature mismatch | Release vs debug on device | `adb uninstall` + `adb install -r` |
| Maestro iOS “0 devices” | Maestro + iOS 26.5 simulator pairing | Prefer **XCUITest** locally; Maestro on CI macos-15 |
| CoreSimulator Mach -308 | Simulator wedged after tooling | `run-ios-xctest.sh` resets simulators before run |

---

## Why it *feels* bad

1. **False confidence** — Android device job name says Maestro; CI runs instrumentation only.
2. **Local pain ≠ CI failure** — CEO machine has JDK/simulator issues CI runners don’t hit.
3. **Many workflows, one story** — `ci`, `device-tests`, `flaky-test-audit`, release, store verify; hard to see “what must be green.”
4. **80% coverage aspirational** — measured **~66%** on `scripts/`; gate not wired.
5. **iOS cost** — 50 min timeout, no cancel; correct choice for stability but slow feedback.
6. **PR cancel** on `ci.yml` — new push aborts runs; fine for unit tests, confusing when combined with long uncancelled device jobs.

---

## Remediation plan (phased)

### Phase A — Environment parity (done on branch)

- [x] `scripts/device-tests/bootstrap-macos.sh` — JDK 21, Maestro, remove daemon JVM pin
- [x] `scripts/device-tests/lib/common.sh` — Java + Gradle daemon pin bypass
- [x] `run-ios-xctest.sh` — local iOS E2E without Maestro device discovery
- [x] `ci-maestro.sh` — Compose smoke + Maestro `ci-smoke-emulator.yaml` (no `clearState` on API 30 emulator)
- [x] `device-tests.yml` — Java **21**; job renamed **Compose + Maestro Smoke**

### Phase B — Honest gates (in progress)

- [x] `--cov-fail-under=66` in `ci.yml` + `pyproject.toml` (floor; target 80 in `ci-config.yml`)
- [x] `.maestro/config.yaml` workspace baseline
- [ ] Raise floor 66 → 70 → 80 as tests land (see `docs/reports/technical-debt-audit-2026-05-26.md`)

### Phase C — Scale (later)

- Maestro sharding for nightly; PR stays smoke-only
- Quarantine file for flaky flows (`@quarantine` tag + `excludeTags`)
- Optional: drop Agent Device from PR path if Maestro assertions suffice (cuts iOS minutes)

---

## Accurate status statement

**CI merge health on `develop` is good for current required checks.**  
**Local mobile E2E was broken for fixable toolchain reasons, not because the app is untestable.**  
**Our largest gap vs top teams is parity and enforcement (Maestro on CI Android, coverage gate, single runner contract) — not absence of automation.**
