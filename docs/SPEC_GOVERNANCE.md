# Spec Governance (lite) — when SDD pays off

Source: [When Spec-Driven Development Pays Off (InfoQ, 2026-09-10)](https://www.infoq.com/articles/when-spec-driven-development-pays-off/) — Nitin Garg.

Complements (does not replace) Spec Kit: `docs/SPEC_KIT.md` / `scripts/speckit_gate.py`.

## What the study actually bought

Core ROI: **attribution** (named invariant), not higher recall.


| Claim | Measured outcome |
|-------|------------------|
| Spec baseline catches more bugs | **No** — recall ≈ flat |
| Spec baseline makes findings attributable | **Yes** — named invariant / clause |
| Spec-in-same-prompt ≈ code-only | **Yes** — delivery mode matters |
| Staged approved baseline → fresh generate | Moves hard-task pass rate |
| Easy-task “spec first” gains | Mostly **reasoning effect** |

## Targeting rule (high ROI)

**Use full spec governance when:** hard, multi-constraint, long-lived work (paywall/entitlements, store release integrity, multi-invariant domain logic) on a capable-but-imperfect model.

**Skip / reason-first when:** typos, README, throwaway scripts, tasks the assistant reliably one-shots.

## Five control points

1. **Specification authoring** — draft baseline (spec + interfaces + testable invariants)
2. **Specification review gate** — approved baseline (approver + timestamp)
3. **Guided generation** — generate from approved docs; generation record (baseline version + model)
4. **Drift detection** — compare code to baseline; drift log (divergence + violated clause)
5. **Reconciliation** — human resolves each drift; reconciliation record (what/why/who)

## Accountability (RACI)

Keep the **human accountable** for drift reconciliation.


- Model: **Responsible** for generation — never **Accountable**
- Human (CEO / CTO judgment): **Accountable** for meaningful drift decisions

## Fitness

```bash
python3 scripts/spec_governance_gate.py --json
python3 scripts/spec_governance_gate.py --json --task "paywall gate with catalog load"
```

## Bridge to Spec Kit

| Hardness | Default path |
|----------|----------------|
| hard | Spec Kit specify→plan→tasks→implement→converge + named invariants in `spec.md` |
| easy | Reason-first; optional Spec Kit |
| medium | Spec Kit when intent must survive review; else reason-first |

## Explicitly rejected

- Mandating full SDD ceremony for every chore
- Claiming “we have a spec” when it lived only inside one prompt
- Treating the model as the accountable party for production behavior
