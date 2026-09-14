# Local-First Hybrid Router

Selectively local on 16GB Macs: private and low-stakes work stays local;
hard public reasoning escalates to frontier APIs under the **$20**/mo fleet cap.

Source framing: *16GB Is All You Need for Serious AI*  
https://music.youtube.com/watch?v=qILTuXLxfBM

## Principles

1. Hybrid router — not wholesale cloud replacement  
2. Task classification before model choice  
3. Private-data lane always local  
4. Optimize workflow before buying RAM  
5. Log cost, latency, acceptance — cut losers after 2–4 weeks  
6. Human approval for commits, payments, outreach, production  

## CLI

```bash
python3 scripts/agent_local_first_router.py route \
  --task-type extraction --confidence 0.8 --complexity 0.2 --json

python3 scripts/agent_local_first_router.py route \
  --task-type architecture --complexity 0.9 --confidence 0.2 --json

python3 scripts/agent_local_first_router.py route \
  --task-type architecture --private --json

python3 scripts/agent_local_first_router.py template \
  --task-type simple_coding --hitl --json

python3 scripts/agent_local_first_router.py summary \
  --log marketing/data/local_first_runs.jsonl --json
```

## Template pipeline

`classify → retrieve_context → local_draft → [cloud_escalate] → human_approval → log_acceptance`

Related: `scripts/agent_deepseek_v4_router.py`, `scripts/agent_open_weight_cost.py`, `scripts/agent_tool_bakeoff.py`.

GSD: `marketing/data/agent_local_first_router.json`
