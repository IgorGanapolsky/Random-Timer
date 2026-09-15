# Agent coding stack (SSOT)

This is Random Timer’s answer to “which LLM framework?” — **none as a universal winner**. We layer a **coding-agent workflow stack** on top of durable repo contracts. Not LangGraph; not an agent runtime.

Canonical recommendation this file encodes (successor-aware):

- Do **not** use archived [`gsd-build/get-shit-done`](https://github.com/gsd-build/get-shit-done) — use [`open-gsd/gsd-core`](https://github.com/open-gsd/gsd-core).
- Treat **AGENTS.md / CLAUDE.md** as the invariant repo contract.
- Layer planning/artifacts, then rigor, then compound learnings.

## Verdict map (job → default)

| Need | Default here | Evidence |
|------|----------------|----------|
| Solo / long-running features | **OpenGSD (gsd-core)** | `docs/GSD_OPENGSD.md`, `python3 scripts/gsd_phase_gate.py --json` |
| Auditable feature specs | **GitHub Spec Kit** | `docs/SPEC_KIT.md`, `python3 scripts/speckit_gate.py --json` |
| When SDD pays off (hard work) | **Spec governance lite** | `docs/SPEC_GOVERNANCE.md`, `python3 scripts/spec_governance_gate.py --json` |
| Highest SE rigor (TDD/worktrees/review) | **Superpowers** | `docs/SUPERPOWERS.md`, `python3 scripts/superpowers_gate.py --json` |
| Product-scale discovery→QA | **BMAD-lite** (not full install) | `docs/BMAD.md`, `python3 scripts/bmad_readiness_gate.py --json` |
| Capture repeated corrections | **Compound Engineering lite** | `docs/COMPOUND_ENGINEERING.md`, `python3 scripts/compound_gate.py --json` |
| Principle-steered rigor / anti-slop | **pstack lite** (poteto-mode) | `docs/PSTACK.md`, `python3 scripts/pstack_gate.py --json` |
| Value-center / agency+coherence | **Value Center lite** (Rohrer VSM) | `docs/VALUE_CENTER.md`, `python3 scripts/value_center_gate.py --json` |
| Escape AI pilot purgatory | **Workflow Economics lite** | `docs/WORKFLOW_ECONOMICS.md`, `python3 scripts/workflow_economics_gate.py --json` |
| Human integrity standard for agents | **Agent Integrity lite** (Terra / CTech) | `docs/AGENT_INTEGRITY.md`, `python3 scripts/agent_integrity_gate.py --json` |
| AI output vs maintainability | **Maintainability Gap lite** (GitClear / TNS) | `docs/MAINTAINABILITY_GAP.md`, `python3 scripts/maintainability_gap_gate.py --json` |
| Durable AI ROI / Diff Delta | **Diff Delta lite** (GitClear.com) | `docs/DIFF_DELTA.md`, `python3 scripts/diff_delta_gate.py --json` |
| Execution runtime (model-separable) | **Cursor / Claude Code / Codex** (+ optional OpenCode) | Host tools; OpenCode CLI may exist locally |
| Hawk metrics / lifecycle ROI | PlayerZero **method** only | `docs/AGENT_COMPOUNDING_ROI.md` |

## Layered stack (do not pick only one)

```text
AGENTS.md + CLAUDE.md          ← invariant contract
        │
        ├─ OpenGSD             ← everyday phase loop (.planning/)
        ├─ Spec Kit + BMAD-lite← feature SPEC / plan / tasks (specs/)
        ├─ Superpowers         ← process skills (TDD, worktrees, verify)
        ├─ pstack lite         ← 23 principles + poteto-mode + unslop
        └─ Compound lite       ← docs/solutions/ after non-trivial work
```

### When to use which

1. **Default feature / refactor / migration** → OpenGSD discuss→plan→execute→verify→ship.
2. **Correctness / high-risk code** → Superpowers TDD + worktree + verification-before-completion; start with poteto-mode.
3. **Shared / auditable specs** → Spec Kit constitution + `specs/<###>/`.
4. **Quick vs Full planning** → BMAD-lite five-element `SPEC.md` readiness gate.
5. **Same mistake twice** → Compound lite write-up under `docs/solutions/` (encode-lessons-in-structure).
6. **Steer with principle names** → pstack lite (`prove it works`, `subtract before you add`, …).
## Explicitly rejected

| Temptation | Why rejected |
|------------|--------------|
| `gsd-build/get-shit-done` | Archived 2026-06-26; successor is open-gsd/gsd-core |
| Full `bmad-method` install | Overlaps Spec Kit / Superpowers; we keep lite contract + gate |
| Full EveryInc Compound plugin (33 skills + reviewer farm) | Token/churn cost; fourth step only |
| “Just prompt harder” / Ralph with no anchors | Expensive wrong cascades |
| Claiming one framework is “best LLM framework” | Wrong category — these are workflow layers |

## Presence gate

```bash
python3 scripts/agent_coding_stack_gate.py --json
```

`ready=true` means all layer docs + scripts exist and child gates report healthy **presence** (not “an active GSD phase is ship-ready”).

## Adoption artifacts

- `marketing/data/opengsd_adoption.json`
- `marketing/data/speckit_adoption.json`
- `marketing/data/superpowers_adoption.json`
- `marketing/data/bmad_adoption.json`
- `marketing/data/compound_engineering_adoption.json`
- `marketing/data/agent_coding_stack_adoption.json`
- `marketing/data/value_center_adoption.json`
- `marketing/data/spec_governance_adoption.json`
- `marketing/data/workflow_economics_adoption.json`
- `marketing/data/agent_integrity_adoption.json`
- `marketing/data/maintainability_gap_adoption.json`
- `marketing/data/diff_delta_adoption.json`

## pstack lite

Rigor principles + poteto-mode: see `docs/PSTACK.md` and `python3 scripts/pstack_gate.py --json`.

## Value Center lite

Agency + coherence (InfoQ Rohrer VSM): see `docs/VALUE_CENTER.md` and `python3 scripts/value_center_gate.py --json`.

## Workflow Economics lite

Escape AI pilot purgatory (completion loop + economic metrics): see `docs/WORKFLOW_ECONOMICS.md` and `python3 scripts/workflow_economics_gate.py --json`.

## Agent Integrity lite

Human is the standard agents are held to (Terra / CTech): see `docs/AGENT_INTEGRITY.md` and `python3 scripts/agent_integrity_gate.py --json`.

## Maintainability Gap lite

Counter AI copy-paste sprawl (+25% output, +81% duplication): see `docs/MAINTAINABILITY_GAP.md` and `python3 scripts/maintainability_gap_gate.py --json`.

## Diff Delta lite

Score durable Diff Delta / production yield (not tokens): see `docs/DIFF_DELTA.md` and `python3 scripts/diff_delta_gate.py --json`.
