# Agent Cost & Reliability Audit

Operational playbook from the 2026 AI budget / “lazy agents” themes: measure completion and unit economics before scaling agent spend. Hard external fleet cap remains **$20 USD/month**.

## Goals

1. Raise task **completion rate** (acceptance criteria met) without babysitting.
2. Cut wasted inference via cost routing and deterministic SQL/code first.
3. Automate only workflows with positive human-vs-model ROI under the $20 cap.

## CLI (zero extra SaaS)

```bash
python3 scripts/agent_cost_reliability_audit.py \
  --platform local_cost_reliability_audit \
  --monthly-frequency 20 \
  --human-minutes 25 \
  --human-usd-per-hour 50 \
  --model-usd 0.08 \
  --review-minutes 5 \
  --month-to-date-usd 4.0 \
  --json
```

Optional local JSON inspect (DuckDB if installed, else SQLite):

```bash
python3 scripts/agent_cost_reliability_audit.py \
  --inspect-json path/to/events.json \
  --sql "SELECT * FROM events LIMIT 5" \
  --json
```

## Library API

| Function | Purpose |
|----------|---------|
| `score_run_completion` | Block incomplete runs without criteria + evidence |
| `classify_laziness` | `ok` / `incomplete_acceptance` / `stopped_at_diagnosis` / `babysitting_escalation` / `missing_evidence` |
| `retry_policy` | Cap retries; escalate only on exceptions |
| `evaluate_automation_roi` | Reject if over $20 fleet remaining or negative unit economics |
| `inspect_json_rows_with_sql` | Cheap structured inspect before costly models |
| `summarize_tool_trace` | Completion rate + cost per successful outcome |
| `audit_workflow` | Combined laziness + completion + ROI + trace |

## Platform gate

Allow local audit markers (`local_cost_reliability_audit`, `duckdb_local`, …). Deny paid managed agent stacks (Bedrock Agents, SageMaker managed agents, LangSmith cloud, etc.) under the $20 cap.

## Evidence rule

Never claim “agents are reliable” without:

- completion rate on a defined acceptance checklist,
- cost per successful outcome,
- top failure modes from tool traces.

GSD artifact: `marketing/data/agent_cost_reliability_audit.json`.
