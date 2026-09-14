---
name: obra-superpowers
description: Use obra/superpowers process skills (verify, TDD, debug, worktrees, subagents) with Random Timer Spec Kit and OpenGSD bridges; run scripts/superpowers_gate.py before claiming harness ready.
---

# obra/superpowers

Upstream: https://github.com/obra/superpowers (v6.3.0)

## When

Starting non-trivial work, debugging, claiming done, or dispatching subagents.

## Steps

1. Follow `using-superpowers` — invoke the matching process skill first.
2. Bugs → `systematic-debugging`. Features → `brainstorming` then Spec Kit specify/plan.
3. Implementation → `test-driven-development` + worktree skills.
4. Before done → `verification-before-completion` AND Spec Kit / OpenGSD gates as applicable.
5. `python3 scripts/superpowers_gate.py --json` must be `ready=true` for harness claims.

## Do not

- Skip verification-before-completion.
- Enable Superpowers visual companion traffic.
- Treat Superpowers as a replacement for Spec Kit artifact paths or OpenGSD `.planning/`.
