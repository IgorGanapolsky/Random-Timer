---
name: agent-access-governance-lite
description: Govern agent permissions — inventory, least privilege, MCP/tool policy, approval gates, audit logs, maturity model (docs/AGENT_ACCESS_GOVERNANCE.md).
---

# Skill: agent-access-governance-lite

Follow `docs/AGENT_ACCESS_GOVERNANCE.md`.

```bash
python3 scripts/agent_access_governance_gate.py --json
```

Rules:
1. Inventory agents, MCP servers, APIs, and service accounts before expanding access.
2. Least privilege + role/attribute/policy controls on every tool call.
3. Human approval + immutable audit for payments, customer outbound, prod changes, exports, destructive ops.
4. Sell risk-reduction/enablement — not generic AI security.
5. No paid governance SaaS default under the $20/mo hard cap.
