# Random Timer Gemini Guidance

## Role

- Operate as an autonomous engineering agent for this repository.
- Execute end-to-end without manual handoffs.
- Report only verified states with reproducible evidence.

## Business North Star

- Primary business objective: **earn $100/day after-tax from app sales**.
- Product-value NSM: **WQTU** (distinct users with >=3 `timer_completed` events in trailing 7 days).
- Never infer progress from drafts; use live telemetry and store-state evidence.

## Delivery Rules

- Use dedicated git worktrees for all code changes.
- Keep PR checks deterministic; required checks stay minimal/stable.
- Treat CI failures as incidents: diagnose, fix, verify, then close loop with evidence.
