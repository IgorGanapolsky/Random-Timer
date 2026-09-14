# AI employees (not agents)

Episode framing: [AI employees, not agents](https://music.youtube.com/watch?v=LE0LNULrsEM)

## Posture

Ship **one or two narrowly scoped operational workers** with:

- a versioned **role contract** (inputs, tools, outputs, escalation, quality bar, KPIs)
- **draft-only** external actions until human approval
- **allowlisted** systems of record (Gmail, Calendar, CRM, Notion/Linear, GitHub, Slack, Drive)
- durable **business memory**
- outcome KPIs (acceptance, edit distance, factual errors, time, cost, revenue influenced)
- a **5x ROI** scale/kill gate under the **$20/mo** fleet cap

Do **not** build multi-agent swarms, generic research agents, or unbounded browser/computer control before a single worker loop proves outcomes.

## Seeded employees

| ID | Job | Primary outcomes |
|---|---|---|
| `consulting_sales_engineer` | Lead → account brief → outreach → proposal brief | Pipeline / proposal turnaround |
| `delivery_manager` | Meetings + GitHub/Linear → weekly status pack | Hours saved / client-ready updates |

## CLI

```bash
python3 scripts/agent_ai_employees.py doctor
python3 scripts/agent_ai_employees.py list --kind employees
python3 scripts/agent_ai_employees.py list --kind playbooks
python3 scripts/agent_ai_employees.py run --employee-id delivery_manager --input-json /tmp/in.json
python3 scripts/agent_ai_employees.py summary --log /tmp/employee_runs.jsonl
python3 scripts/agent_ai_employees.py roi --cost-usd 100 --value-usd 600
```

## 30-day operating plan

1. Week 1 — pick one 3–5h/week workflow; baseline time/quality/errors  
2. Week 2 — smallest end-to-end draft worker + mandatory approval  
3. Week 3 — wire sources of truth + memory + logs; 20–30 cases  
4. Week 4 — KPI review; scale / redesign / kill at 5x ROI  

## Evidence status

Code + unit tests landed. Live 30-day KPI / revenue-influenced outcomes: **not verified** until runs are logged against real work.
