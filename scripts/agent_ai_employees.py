"""AI employees (bounded workers), not open-ended agents.

Episode framing: “AI employees, not agents”
https://music.youtube.com/watch?v=LE0LNULrsEM

Highest-ROI posture: one or two narrowly scoped operational workers with
role contracts, draft-only external actions, systems-of-record allowlists,
durable business memory, and outcome KPIs — not a multi-agent platform.

Fleet cap: FLEET_MONTHLY_CAP_USD ($20). Kill/redesign below MIN_ROI_MULTIPLE.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

FLEET_MONTHLY_CAP_USD = 20.0
MIN_ROI_MULTIPLE = 5.0
CONTRACT_VERSION = "1.0.0"

ALLOWED_PLATFORMS = frozenset(
    {
        "ai_employees",
        "agent_ai_employees",
        "ai_employee",
        "bounded_ai_worker",
    }
)
MULTI_AGENT_MARKERS = (
    "multi_agent_swarm",
    "unbounded_multi_agent",
    "agent_swarm",
    "orchestration_platform",
    "autonomous_company",
)
GENERIC_RESEARCH_MARKERS = (
    "generic_research_agent",
    "open_ended_research",
    "research_agent_only",
    "info_without_action",
)

ALLOWED_CONNECTORS = frozenset(
    {
        "gmail",
        "calendar",
        "crm",
        "notion",
        "linear",
        "github",
        "slack",
        "drive",
    }
)
FORBIDDEN_CONNECTORS = frozenset(
    {
        "unbounded_browser",
        "computer_control_all",
        "admin_billing",
        "production_deploy_without_approval",
    }
)


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str
    score: float = 0.0


@dataclass(frozen=True)
class RoleContract:
    version: str
    role: str
    business_outcome: str
    inputs: tuple[str, ...]
    permitted_tools: tuple[str, ...]
    output_format: tuple[str, ...]
    escalation_conditions: tuple[str, ...]
    quality_bar: tuple[str, ...]
    kpis: tuple[str, ...]
    draft_only_actions: tuple[str, ...]


@dataclass(frozen=True)
class Employee:
    employee_id: str
    contract: RoleContract


@dataclass(frozen=True)
class Playbook:
    playbook_id: str
    employee_id: str
    steps: tuple[str, ...]
    outcome_metric: str


@dataclass
class EmployeeRun:
    ok: bool
    employee_id: str
    status: str
    outputs: dict[str, Any] = field(default_factory=dict)
    action: str = ""
    reason: str = ""
    contract_version: str = CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _norm(value: str) -> str:
    return (
        (value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(".", "_")
        .replace(" ", "_")
    )


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_ai_employees",
            ok=True,
            reason="bounded AI employee posture under fleet cap",
        )
    if any(marker in name for marker in MULTI_AGENT_MARKERS):
        return ControlDecision(
            action="block_multi_agent_swarm",
            ok=False,
            reason="prove one worker loop before multi-agent orchestration",
        )
    if any(marker in name for marker in GENERIC_RESEARCH_MARKERS):
        return ControlDecision(
            action="block_generic_research_agent",
            ok=False,
            reason="reject research without a named business downstream action",
        )
    return ControlDecision(
        action="block_unknown_platform",
        ok=False,
        reason="unknown AI-employee platform denied",
    )


def _sales_contract() -> RoleContract:
    return RoleContract(
        version=CONTRACT_VERSION,
        role="AI consulting / sales engineer",
        business_outcome="qualified pipeline and proposal turnaround",
        inputs=(
            "prospect_name",
            "icp_fit_notes",
            "offer",
            "prior_touchpoints",
        ),
        permitted_tools=("gmail", "crm", "calendar", "github", "drive"),
        output_format=(
            "account_brief",
            "qualification",
            "outreach_sequence",
            "proposal_brief",
            "crm_update_draft",
        ),
        escalation_conditions=(
            "pricing_exception",
            "legal_terms",
            "send_email",
            "crm_write",
            "calendar_invite",
        ),
        quality_bar=(
            "named_business_outcome",
            "tailored_to_prospect",
            "no_fabricated_facts",
            "draft_only_until_approval",
        ),
        kpis=(
            "acceptance_rate",
            "edit_distance",
            "proposal_turnaround_sec",
            "qualified_meetings_booked",
            "revenue_influenced_usd",
            "cost_per_completed_task",
        ),
        draft_only_actions=("send_email", "crm_write", "calendar_invite"),
    )


def _delivery_contract() -> RoleContract:
    return RoleContract(
        version=CONTRACT_VERSION,
        role="AI delivery manager",
        business_outcome="faster client-ready status with lower PM overhead",
        inputs=(
            "meeting_notes",
            "github_activity",
            "stakeholder_messages",
            "linear_or_notion_items",
        ),
        permitted_tools=("github", "linear", "notion", "slack", "gmail", "drive"),
        output_format=(
            "weekly_status",
            "risks",
            "decision_log",
            "next_actions",
            "client_update_draft",
        ),
        escalation_conditions=(
            "client_facing_send",
            "scope_change",
            "production_change",
            "payment_or_contract",
        ),
        quality_bar=(
            "evidence_linked",
            "risks_named",
            "owners_and_dates",
            "draft_only_until_approval",
        ),
        kpis=(
            "acceptance_rate",
            "edit_distance",
            "hours_saved",
            "factual_error_rate",
            "cost_per_completed_task",
        ),
        draft_only_actions=("client_facing_send", "slack_post", "github_comment"),
    )


_EMPLOYEES: dict[str, Employee] = {
    "consulting_sales_engineer": Employee(
        employee_id="consulting_sales_engineer",
        contract=_sales_contract(),
    ),
    "delivery_manager": Employee(
        employee_id="delivery_manager",
        contract=_delivery_contract(),
    ),
}

_PLAYBOOKS: tuple[Playbook, ...] = (
    Playbook(
        playbook_id="lead_to_proposal",
        employee_id="consulting_sales_engineer",
        steps=(
            "ingest_prospect",
            "qualify_icp",
            "draft_account_brief",
            "draft_outreach",
            "draft_proposal_brief",
            "human_approval",
            "log_kpis",
        ),
        outcome_metric="proposal_turnaround_sec",
    ),
    Playbook(
        playbook_id="discovery_to_sow",
        employee_id="consulting_sales_engineer",
        steps=(
            "ingest_discovery_notes",
            "map_pain_to_offer",
            "draft_sow",
            "human_approval",
            "log_kpis",
        ),
        outcome_metric="revenue_influenced_usd",
    ),
    Playbook(
        playbook_id="meeting_to_execution",
        employee_id="delivery_manager",
        steps=(
            "ingest_meeting_and_systems",
            "extract_decisions_risks_actions",
            "draft_weekly_status",
            "human_approval",
            "log_kpis",
        ),
        outcome_metric="hours_saved",
    ),
)


def list_employees() -> list[Employee]:
    return [ _EMPLOYEES[k] for k in sorted(_EMPLOYEES) ]


def get_employee(employee_id: str) -> Employee:
    key = _norm(employee_id)
    if key not in _EMPLOYEES:
        raise KeyError(employee_id)
    return _EMPLOYEES[key]


def list_playbooks() -> list[Playbook]:
    return list(_PLAYBOOKS)


def _require_inputs(contract: RoleContract, inputs: Mapping[str, Any]) -> None:
    missing = [k for k in contract.inputs if k not in inputs or inputs[k] in (None, "")]
    # Allow optional trailing inputs without blocking MVP runs.
    required = contract.inputs[:3]
    missing_required = [k for k in required if k not in inputs or inputs[k] in (None, "")]
    if missing_required:
        raise ValueError(f"missing required inputs: {missing_required}")


def _draft_sales(inputs: Mapping[str, Any]) -> dict[str, Any]:
    prospect = str(inputs.get("prospect_name", "")).strip()
    fit = str(inputs.get("icp_fit_notes", "")).strip()
    offer = str(inputs.get("offer", "")).strip()
    return {
        "account_brief": (
            f"Account: {prospect}. Fit notes: {fit}. "
            f"Opportunity: map pains to `{offer}` with a bounded AI-employee pilot."
        ),
        "qualification": {
            "fit": "qualified" if fit else "needs_more_info",
            "reason": fit or "missing ICP notes",
        },
        "outreach_sequence": [
            {
                "day": 0,
                "channel": "email",
                "subject": f"Quick idea for {prospect}: bounded AI employee, not another agent",
                "body": (
                    f"Saw {prospect} wrestling with automation overhead. "
                    f"We install one measurable worker around `{offer}` with "
                    "draft-only approvals and outcome KPIs."
                ),
            },
            {
                "day": 3,
                "channel": "email",
                "subject": f"Follow-up: 30-day AI employee pilot for {prospect}",
                "body": "Happy to share the role contract + scorecard before any send/write automation.",
            },
        ],
        "proposal_brief": {
            "title": f"{offer} for {prospect}",
            "scope": [
                "Role contract + approval gate",
                "Systems-of-record connectors (allowlisted)",
                "KPI dashboard for acceptance, time, cost, revenue influenced",
            ],
            "success_metric": ">=5x return on tool+engineering cost in 30 days",
        },
        "crm_update_draft": {
            "stage": "proposal_draft",
            "next_step": "human approve outreach",
            "notes": fit,
        },
    }


def _draft_delivery(inputs: Mapping[str, Any]) -> dict[str, Any]:
    notes = str(inputs.get("meeting_notes", "")).strip()
    github = str(inputs.get("github_activity", "")).strip()
    msgs = str(inputs.get("stakeholder_messages", "")).strip()
    return {
        "weekly_status": (
            f"Status draft from notes/systems. Meetings: {notes}. "
            f"GitHub: {github}. Stakeholders: {msgs}."
        ),
        "risks": [
            item.strip()
            for item in notes.replace(";", ".").split(".")
            if "risk" in item.lower()
        ]
        or ["No explicit risks parsed; confirm with owner."],
        "decision_log": [
            {
                "decision": "Prefer AI employees over open-ended agents",
                "evidence": "episode framing + operating plan",
            }
        ],
        "next_actions": [
            "Human review weekly_status draft",
            "Confirm owners/dates for open risks",
            "Log acceptance + edit distance after review",
        ],
        "client_update_draft": (
            "Client-ready update (draft): progress, risks, and next actions "
            "awaiting approval before send."
        ),
    }


def run_employee(
    *,
    employee_id: str,
    inputs: Mapping[str, Any],
    approve: bool = False,
) -> EmployeeRun:
    emp = get_employee(employee_id)
    # Guard connectors against forbidden tools in contract.
    bad = set(emp.contract.permitted_tools) & FORBIDDEN_CONNECTORS
    if bad:
        return EmployeeRun(
            ok=False,
            employee_id=emp.employee_id,
            status="blocked",
            action="block_forbidden_connector",
            reason=f"forbidden connectors in contract: {sorted(bad)}",
        )
    unknown = set(emp.contract.permitted_tools) - ALLOWED_CONNECTORS
    if unknown:
        return EmployeeRun(
            ok=False,
            employee_id=emp.employee_id,
            status="blocked",
            action="block_unknown_connector",
            reason=f"unknown connectors: {sorted(unknown)}",
        )

    _require_inputs(emp.contract, inputs)

    if emp.employee_id == "consulting_sales_engineer":
        outputs = _draft_sales(inputs)
    elif emp.employee_id == "delivery_manager":
        outputs = _draft_delivery(inputs)
    else:  # pragma: no cover - guarded by registry
        raise KeyError(employee_id)

    status = "approved" if approve else "draft_pending_approval"
    return EmployeeRun(
        ok=True,
        employee_id=emp.employee_id,
        status=status,
        outputs=outputs,
        action="draft_outputs" if not approve else "approved_outputs",
        reason="draft-only external actions until human approval",
        contract_version=emp.contract.version,
    )


def apply_approval(
    *,
    draft: EmployeeRun,
    decision: str,
    approved: bool,
) -> EmployeeRun:
    decision_n = _norm(decision)
    if decision_n in {"send", "crm_write", "publish", "deploy"} and not approved:
        return EmployeeRun(
            ok=False,
            employee_id=draft.employee_id,
            status="blocked",
            outputs=dict(draft.outputs),
            action="block_unapproved_external_write",
            reason="external write requires explicit human approval",
            contract_version=draft.contract_version,
        )
    if not approved and decision_n not in {"edit", "reject"}:
        return EmployeeRun(
            ok=False,
            employee_id=draft.employee_id,
            status="blocked",
            outputs=dict(draft.outputs),
            action="block_unapproved_external_write",
            reason="approval flag false",
            contract_version=draft.contract_version,
        )
    if decision_n == "reject":
        return EmployeeRun(
            ok=True,
            employee_id=draft.employee_id,
            status="rejected",
            outputs=dict(draft.outputs),
            action="rejected",
            reason="human rejected draft",
            contract_version=draft.contract_version,
        )
    return EmployeeRun(
        ok=True,
        employee_id=draft.employee_id,
        status="approved",
        outputs=dict(draft.outputs),
        action="approved",
        reason=f"human decision={decision_n}",
        contract_version=draft.contract_version,
    )


def save_memory(*, path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "clients": list(record.get("clients") or []),
        "icp": record.get("icp") or "",
        "offers": list(record.get("offers") or []),
        "projects": list(record.get("projects") or []),
        "decisions": list(record.get("decisions") or []),
        "brand_voice": record.get("brand_voice") or "",
        "pricing": dict(record.get("pricing") or {}),
        "prior_outputs": list(record.get("prior_outputs") or []),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_memory(*, path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def log_run(
    *,
    path: Path,
    employee_id: str,
    task_completed: bool,
    accepted: bool,
    edit_distance: float,
    factual_error: bool,
    elapsed_sec: float,
    cost_usd: float,
    revenue_influenced_usd: float = 0.0,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "employee_id": employee_id,
        "task_completed": bool(task_completed),
        "accepted": bool(accepted),
        "edit_distance": float(edit_distance),
        "factual_error": bool(factual_error),
        "elapsed_sec": float(elapsed_sec),
        "cost_usd": float(cost_usd),
        "revenue_influenced_usd": float(revenue_influenced_usd),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def summarize_kpis(*, path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    n = len(rows)
    if n == 0:
        return {
            "runs": 0,
            "acceptance_rate": 0.0,
            "avg_edit_distance": 0.0,
            "factual_error_rate": 0.0,
            "avg_elapsed_sec": 0.0,
            "avg_cost_usd": 0.0,
            "revenue_influenced_usd": 0.0,
        }
    accepted = sum(1 for r in rows if r.get("accepted"))
    factual_errors = sum(1 for r in rows if r.get("factual_error"))
    return {
        "runs": n,
        "acceptance_rate": accepted / n,
        "avg_edit_distance": sum(float(r.get("edit_distance", 0)) for r in rows) / n,
        "factual_error_rate": factual_errors / n,
        "avg_elapsed_sec": sum(float(r.get("elapsed_sec", 0)) for r in rows) / n,
        "avg_cost_usd": sum(float(r.get("cost_usd", 0)) for r in rows) / n,
        "revenue_influenced_usd": sum(
            float(r.get("revenue_influenced_usd", 0)) for r in rows
        ),
    }


def evaluate_roi_gate(
    *,
    engineering_and_tool_cost_usd: float,
    measured_value_usd: float,
) -> ControlDecision:
    cost = float(engineering_and_tool_cost_usd)
    value = float(measured_value_usd)
    if cost <= 0:
        return ControlDecision(
            action="block_invalid_cost",
            ok=False,
            reason="engineering_and_tool_cost_usd must be > 0",
            score=0.0,
        )
    multiple = value / cost
    if multiple >= MIN_ROI_MULTIPLE:
        return ControlDecision(
            action="scale",
            ok=True,
            reason=f"measured ROI {multiple:.2f}x meets {MIN_ROI_MULTIPLE:.0f}x gate",
            score=multiple,
        )
    return ControlDecision(
        action="kill_or_redesign",
        ok=False,
        reason=f"measured ROI {multiple:.2f}x below {MIN_ROI_MULTIPLE:.0f}x gate",
        score=multiple,
    )


def thirty_day_plan() -> dict[str, Any]:
    return {
        "week_1": "Pick one 3–5h/week workflow; baseline time, quality, errors",
        "week_2": "Smallest end-to-end draft worker + mandatory human approval",
        "week_3": "Wire systems of record + memory + run logs; 20–30 cases",
        "week_4": "KPI review; scale / redesign / kill using 5x ROI gate",
        "rule": "Hire for a job with evidence — do not ask what an agent can do",
    }


def doctor() -> dict[str, Any]:
    return {
        "ok": True,
        "module": "scripts/agent_ai_employees.py",
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "min_roi_multiple": MIN_ROI_MULTIPLE,
        "employees": [e.employee_id for e in list_employees()],
        "playbooks": [p.playbook_id for p in list_playbooks()],
        "thirty_day_plan": thirty_day_plan(),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI employees: bounded workers with contracts and approvals"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Show posture and seeded employees")

    p_list = sub.add_parser("list", help="List employees or playbooks")
    p_list.add_argument("--kind", choices=("employees", "playbooks"), default="employees")
    p_list.add_argument("--json", action="store_true")

    p_run = sub.add_parser("run", help="Run an employee in draft mode")
    p_run.add_argument("--employee-id", required=True)
    p_run.add_argument("--input-json", required=True, help="Path to JSON inputs")
    p_run.add_argument("--approve", action="store_true")
    p_run.add_argument("--json", action="store_true")

    p_kpi = sub.add_parser("summary", help="Summarize KPI log")
    p_kpi.add_argument("--log", required=True, type=Path)
    p_kpi.add_argument("--json", action="store_true")

    p_roi = sub.add_parser("roi", help="Evaluate 5x ROI gate")
    p_roi.add_argument("--cost-usd", type=float, required=True)
    p_roi.add_argument("--value-usd", type=float, required=True)
    p_roi.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "doctor":
        print(json.dumps(doctor(), indent=2))
        return 0

    if args.cmd == "list":
        if args.kind == "playbooks":
            payload = [asdict(p) for p in list_playbooks()]
        else:
            payload = [
                {
                    "employee_id": e.employee_id,
                    "contract": asdict(e.contract),
                }
                for e in list_employees()
            ]
        print(json.dumps(payload, indent=2))
        return 0

    if args.cmd == "run":
        inputs = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
        result = run_employee(
            employee_id=args.employee_id,
            inputs=inputs,
            approve=bool(args.approve),
        )
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.ok else 1

    if args.cmd == "summary":
        print(json.dumps(summarize_kpis(path=args.log), indent=2))
        return 0

    if args.cmd == "roi":
        d = evaluate_roi_gate(
            engineering_and_tool_cost_usd=args.cost_usd,
            measured_value_usd=args.value_usd,
        )
        print(json.dumps(asdict(d), indent=2))
        return 0 if d.ok else 1

    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
