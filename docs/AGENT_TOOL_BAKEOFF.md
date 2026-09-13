# AI Tool Bake-Off

Turn “what AI tools to use” into a **bounded experiment**, not tool shopping.

Source framing: *What to Use the Latest AI Tools For* (The AI Breakdown)  
https://music.youtube.com/watch?v=Y2hE6kYZPg0

Hard fleet cap: **$20 USD/month**. ROI floor: **≥2 hours saved / month** (or quality/speed lift, or a chargeable offer).

## Process

1. Name **one** real bottleneck.  
2. Classify work: `reasoning` | `coding` | `research` | `computer_use` | `automation`.  
3. Run a 60–90 minute bake-off of **two** candidates on the same task. Record setup, usable output rate, correction time, cost/task, repeatability.  
4. Keep the winner only if `evaluate_roi_gate` passes under the fleet cap.  
5. Productionize only with template + structured I/O + validation + run logging + HITL + manual fallback.

## CLI

```bash
python3 scripts/agent_tool_bakeoff.py \
  --bottleneck bounded_github_issue_to_merge_ready_pr \
  --kind coding \
  --a-id cursor_agent --a-usable 0.85 --a-correct 12 --a-cost 0.1 \
  --b-id paste_into_chat --b-usable 0.35 --b-correct 50 --b-cost 0.02 --b-not-repeatable \
  --hours-saved 5 --quality \
  --production-ready \
  --month-to-date-usd 2 \
  --json
```

## Random Timer first experiment

**Bottleneck:** bounded GitHub issue → merge-ready PR with tests (coding).  
**Candidates:** repo agent workflow (Cursor/Claude Code) vs unstructured chat paste.  
**Proof:** merge with green required checks; hours saved vs babysitting.  
**Do not** auto-send outreach via browser agents.

Related: `scripts/agent_pre_recursive_ops.py`, `scripts/agent_cost_reliability_audit.py`.

GSD: `marketing/data/agent_tool_bakeoff.json`.
