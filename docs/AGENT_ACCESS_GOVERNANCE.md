# Agent Access Governance lite

Source: [YouTube Music / podcast thesis](https://music.youtube.com/watch?v=II_xGPfDb6I) — least privilege, role/attribute/policy controls, and a maturity model for **governed AI agents**.

Highest ROI is not RBAC theory. It is **products and services** that control what agents can access and execute in real workflows — so agents can safely move from pilots into operations.

Under the **$20/mo hard cap**: encode inventory, policy, approvals, and audit locally (gates/hooks/ThumbGate). Do not default to paid agent-security SaaS.

## Anti-pattern

Unrestricted tool access + shared admin service accounts + “generic AI security” pitch → pilots that never enter production, or production agents that over-access data.

## Highest-ROI moves (binding)

| Improvement | Why it pays back |
|-------------|------------------|
| Inventory agents, MCP servers, APIs, service accounts | Finds over-permission and approval gaps fast |
| Least-privilege scopes + per-action policies | Shrinks blast radius without killing enablement |
| Tool/MCP policy proxy (allow/deny + log) | Reusable control plane for every agent |
| Approval gates for risky ops | Payments, customer comms, prod changes, exports, destructive |
| Immutable audit logs + risk view | Compliance evidence and executive trust |
| Maturity model path | Assessment → implementation → monitoring upsell |

## Maturity stages

```text
ad_hoc → inventoried → least_privilege → policy_enforced → continuously_monitored
```

## Commercial wedge (when selling outward)

1. Access-governance audit (map agents/tools/identities/permissions/exposure).
2. MCP/API policy proxy with identity propagation and approval callbacks.
3. Permission-aware vertical templates (support read-only CRM; DevOps propose-not-execute).
4. Continuous monitoring / monthly managed governance.
5. Entry: maturity assessment (“Can your AI agents access more than they should?”).

Sell **risk-reduction + enablement**, not generic AI security.

## Random Timer binding

- Risky ops (store publish, billing writes, customer outbound) need approval + audit.
- MCP/tool calls must be policy-checked before execute.
- Prefer existing ThumbGate / CI gates over new paid SaaS.

## Fitness

```bash
python3 scripts/agent_access_governance_gate.py --json
```

## Explicitly rejected

- Unrestricted agent tools / shared admin credentials
- Skipping approvals for payments, prod changes, exports, destructive ops
- Default paid governance SaaS under the monthly hard cap
- Generic “AI security” without inventory, policy, or audit evidence
