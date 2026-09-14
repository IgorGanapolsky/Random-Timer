# Pi YOLO harness (`pi-yolo`)

Smallest high-ROI extract from agentic engineering workflows: a **gated**
plan → implement → test → evidence lane for `issue_to_pr`, not a custom
multi-agent company.

Source framing: https://music.youtube.com/watch?v=SxuQs9GGYbk

## Terminal command

```bash
pi-yolo                 # repo guide JSON
pi-yolo doctor
pi-yolo guide --json
pi-yolo check --plan --yolo --criteria tests_green --criteria evidence_package \
  --worktree --file scripts/agent_pi_yolo.py \
  --test scripts/tests/test_agent_pi_yolo.py --tests-passed \
  --risks-ok --rollback-ok \
  --evidence marketing/data/agent_pi_yolo.json \
  --plan-summary "add pi harness" --rollback "revert merge" --json
```

Install (once): `bin/pi-yolo` is symlinked to `~/.local/bin/pi-yolo` and aliased in `~/.zshrc`.

## Gated loop

1. Agent writes a plan with acceptance criteria  
2. Human approves **or** `--yolo` auto-approves when criteria are explicit  
3. Implement in a worktree/feature branch  
4. Run tests + self-review  
5. Emit evidence package: files changed, tests run, risks, rollback  

## Definition of done

- `files_changed` non-empty  
- tests run and passed  
- risks + rollback notes  
- evidence path present  

## Rules (fail closed)

- No secrets  
- No production/cloud changes from this harness  
- No dependency additions without approval  
- Worktree/branch required  

## KPIs (instrument 5–10 tasks)

- Median minutes to mergeable PR  
- Human review minutes  
- First-pass test pass rate  
- Rework/revert rate  
- Cost per successful task  

Module: `scripts/agent_pi_yolo.py`  
GSD: `marketing/data/agent_pi_yolo.json`
