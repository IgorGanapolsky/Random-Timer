---
name: anti-babysitting-rtt
description: >-
  Random Timer anti-babysitting mandate. Invoke at session start and before any
  turn ending with want-me-to / should-I / say-the-word, or before parking an
  issue as incomplete. Encodes 2026-09-16 GH #1925 failure (CEO had to ask why
  coordination was not finished). Prefer executing closeout with honest grade
  over waiting for 10/10. Do not use to bypass spend caps, outward sends, or
  correctly firing danger gates.
---

# Anti-babysitting — Random Timer

## Failure this prevents

2026-09-16: CEO asked "why can't you take care of #1925" after agents parked
multi-agent coordination behind Notebook UUID / GitButler perfection instead of
closing with evidence and residual child locks.

## Rule

**The CEO never babysits.** Diagnosis without action is failure. Incomplete is
not blocked — ship B+ with owned residuals.

## Before ending any turn

1. Delete any "want me to / should I / say the word / let me know" on pre-authorized work.
2. If a named issue/PR/lock is still open and you can close or advance it, do that now.
3. If auto-review blocked a write, retry once with `requestSmartModeApproval` / `request_smart_mode_approval` — do not abandon.
4. Report receipts (URLs, SHAs, issue state), not a to-do list for the CEO.

## RTT pre-authorized

- Issue/PR hygiene, release-watch closeout, Linear AGENT locks, vault SSOT sync
- Store publish automation already in repo (AFTER_APPROVAL, watchers, hygiene)
- ROSE-lite session refresh; notebook pack_ready registration (live UUID is residual, not a stop)

## Only stop for

Metered over-cap spend · irreversible outward send · human-only credentials · correctly firing danger gate.

## Related

- `.cursor/rules/anti-babysitting.mdc`
- `.claude/rules/anti-babysitting.md`
- User skills: `anti-babysitting-mandate`, `no-babysitting-execute-the-fix`, `never-hand-the-decision-back`
