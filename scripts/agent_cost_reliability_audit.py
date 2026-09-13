"""Agent cost + reliability audit (zero external spend).

Themes from AWS DuckDB / lazy agents / 2026 AI budget reckoning:
1. Fix lazy agents — acceptance criteria, evidence, no babysitting.
2. Budget reckoning — automate only when human cost >> model+review cost.
3. Cheap structured inspect (DuckDB if present, else SQLite) before costly models.
4. Observability — completion rate and cost per successful outcome.

Hard fleet cap: FLEET_MONTHLY_CAP_USD (same $20 operating mandate).
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

FLEET_MONTHLY_CAP_USD = 20.0

ALLOWED_PLATFORMS = frozenset(
    {
        "local_cost_reliability_audit",
        "agent_cost_reliability_audit",
        "local_agent_audit",
        "sqlite_inspect",
        "duckdb_local",
    }
)
DENIED_MARKERS = (
    "bedrock_agents",
    "aws_bedrock_agents",
    "sagemaker_managed_agent",
    "agentcore_paid",
    "langsmith_cloud",
    "databricks",
)


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str
    monthly_net_usd: float = 0.0
    completion_rate: float = 0.0


@dataclass(frozen=True)
class TraceSummary:
    attempts: int
    successes: int
    completion_rate: float
    total_usd: float
    cost_per_success_usd: float
    top_failure: str | None


@dataclass(frozen=True)
class InspectResult:
    ok: bool
    engine: str
    rows: tuple[dict[str, Any], ...]
    reason: str


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
            action="allow_local_audit",
            ok=True,
            reason="local cost/reliability audit under operating cap",
        )
    if any(marker in name for marker in DENIED_MARKERS):
        return ControlDecision(
            action="block_paid_agent_infra",
            ok=False,
            reason="paid/managed agent infra denied under fleet cap",
        )
    return ControlDecision(
        action="block_paid_agent_infra",
        ok=False,
        reason="unknown agent infra denied",
    )


def classify_laziness(
    *,
    acceptance_met: bool,
    evidence_paths: Sequence[str],
    stopped_at_diagnosis: bool,
    asked_human_to_run_commands: bool,
) -> str:
    if asked_human_to_run_commands:
        return "babysitting_escalation"
    if stopped_at_diagnosis:
        return "stopped_at_diagnosis"
    if acceptance_met and evidence_paths:
        return "ok"
    if not acceptance_met:
        return "incomplete_acceptance"
    if not evidence_paths:
        return "missing_evidence"
    return "ok"


def score_run_completion(
    *,
    acceptance_criteria: Sequence[str],
    criteria_met: Sequence[str],
    evidence_paths: Sequence[str],
    tool_calls: int,
) -> ControlDecision:
    required = tuple(c for c in acceptance_criteria if c)
    met = set(criteria_met)
    if not required:
        return ControlDecision(
            action="block_incomplete_run",
            ok=False,
            reason="acceptance criteria required",
            completion_rate=0.0,
        )
    hit = sum(1 for c in required if c in met)
    rate = hit / len(required)
    if rate < 1.0 or not evidence_paths:
        return ControlDecision(
            action="block_incomplete_run",
            ok=False,
            reason="acceptance incomplete or evidence missing",
            completion_rate=rate,
        )
    if tool_calls <= 0:
        return ControlDecision(
            action="block_incomplete_run",
            ok=False,
            reason="no tool activity recorded",
            completion_rate=rate,
        )
    return ControlDecision(
        action="allow_complete_run",
        ok=True,
        reason="acceptance met with evidence",
        completion_rate=rate,
    )


def retry_policy(
    *,
    attempt: int,
    max_attempts: int = 3,
    is_exception: bool = False,
) -> ControlDecision:
    if is_exception:
        return ControlDecision(
            action="escalate_human",
            ok=False,
            reason="exception path — escalate only for exceptions",
        )
    if attempt < max_attempts:
        return ControlDecision(
            action="retry",
            ok=True,
            reason=f"retry attempt {attempt}/{max_attempts}",
        )
    return ControlDecision(
        action="fail_closed",
        ok=False,
        reason="max attempts exhausted without exception escalation",
    )


def evaluate_automation_roi(
    *,
    monthly_frequency: int,
    human_minutes_per_run: float,
    human_usd_per_hour: float,
    model_usd_per_run: float,
    review_minutes_per_run: float,
    month_to_date_spend_usd: float,
    fleet_cap_usd: float = FLEET_MONTHLY_CAP_USD,
) -> ControlDecision:
    if monthly_frequency <= 0:
        return ControlDecision(
            action="block_negative_roi",
            ok=False,
            reason="frequency must be positive",
        )
    human_usd = (human_minutes_per_run / 60.0) * human_usd_per_hour
    review_usd = (review_minutes_per_run / 60.0) * human_usd_per_hour
    savings_per_run = human_usd - (model_usd_per_run + review_usd)
    monthly_net = savings_per_run * monthly_frequency
    projected_spend = month_to_date_spend_usd + (model_usd_per_run * monthly_frequency)
    if projected_spend > fleet_cap_usd:
        return ControlDecision(
            action="block_budget_cap",
            ok=False,
            reason="projected model spend exceeds fleet monthly cap",
            monthly_net_usd=monthly_net,
        )
    if monthly_net <= 0:
        return ControlDecision(
            action="block_negative_roi",
            ok=False,
            reason="human cost does not exceed model+review cost",
            monthly_net_usd=monthly_net,
        )
    return ControlDecision(
        action="automate",
        ok=True,
        reason="unit economics clear under fleet cap",
        monthly_net_usd=monthly_net,
    )


def _load_json_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    raise ValueError("JSON must be an object or array of objects")


def inspect_json_rows_with_sql(*, path: Path, sql: str) -> InspectResult:
    """Cheap structured inspect before invoking costly models.

    Prefers DuckDB when installed; falls back to stdlib SQLite (zero install).
    """
    rows = _load_json_rows(path)
    if not rows:
        return InspectResult(ok=False, engine="none", rows=(), reason="no rows")

    try:
        import duckdb  # type: ignore

        con = duckdb.connect(database=":memory:")
        con.execute("CREATE TABLE events AS SELECT * FROM read_json_auto(?)", [str(path)])
        out = con.execute(sql).fetchall()
        cols = [d[0] for d in con.description]
        records = tuple(dict(zip(cols, row)) for row in out)
        return InspectResult(
            ok=True,
            engine="duckdb",
            rows=records,
            reason="duckdb local inspect",
        )
    except Exception:
        pass

    columns: list[str] = []
    for row in rows:
        for key, value in row.items():
            if key in columns:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                columns.append(key)
    if not columns:
        return InspectResult(ok=False, engine="sqlite", rows=(), reason="no scalar columns")

    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    typed: list[str] = []
    for c in columns:
        nums = [row.get(c) for row in rows if isinstance(row.get(c), (int, float)) and not isinstance(row.get(c), bool)]
        non_null = [row.get(c) for row in rows if row.get(c) is not None]
        if non_null and len(nums) == len(non_null):
            typed.append(f'"{c}" REAL')
        else:
            typed.append(f'"{c}" TEXT')
    con.execute(f'CREATE TABLE events ({", ".join(typed)})')
    placeholders = ", ".join("?" for _ in columns)
    for row in rows:
        values = []
        for c in columns:
            v = row.get(c)
            if isinstance(v, bool):
                values.append(str(v))
            else:
                values.append(v)
        con.execute(f"INSERT INTO events VALUES ({placeholders})", values)
    cur = con.execute(sql)
    records = tuple(dict(r) for r in cur.fetchall())
    return InspectResult(
        ok=True,
        engine="sqlite",
        rows=records,
        reason="sqlite local inspect (duckdb optional)",
    )


def summarize_tool_trace(*, runs: Sequence[Mapping[str, Any]]) -> TraceSummary:
    attempts = len(runs)
    successes = sum(1 for r in runs if r.get("ok"))
    total_usd = float(sum(float(r.get("usd") or 0.0) for r in runs))
    completion = (successes / attempts) if attempts else 0.0
    cps = (total_usd / successes) if successes else float("inf") if total_usd else 0.0
    failures = [str(r.get("failure")) for r in runs if not r.get("ok") and r.get("failure")]
    top = Counter(failures).most_common(1)
    return TraceSummary(
        attempts=attempts,
        successes=successes,
        completion_rate=completion,
        total_usd=total_usd,
        cost_per_success_usd=cps if cps != float("inf") else total_usd,
        top_failure=top[0][0] if top else None,
    )


def audit_workflow(
    *,
    platform: str,
    acceptance_criteria: Sequence[str],
    criteria_met: Sequence[str],
    evidence_paths: Sequence[str],
    tool_calls: int,
    stopped_at_diagnosis: bool,
    asked_human_to_run_commands: bool,
    monthly_frequency: int,
    human_minutes_per_run: float,
    human_usd_per_hour: float,
    model_usd_per_run: float,
    review_minutes_per_run: float,
    month_to_date_spend_usd: float,
    runs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    platform_d = evaluate_platform(platform=platform)
    laziness = classify_laziness(
        acceptance_met=set(criteria_met) >= set(acceptance_criteria) and bool(acceptance_criteria),
        evidence_paths=evidence_paths,
        stopped_at_diagnosis=stopped_at_diagnosis,
        asked_human_to_run_commands=asked_human_to_run_commands,
    )
    completion = score_run_completion(
        acceptance_criteria=acceptance_criteria,
        criteria_met=criteria_met,
        evidence_paths=evidence_paths,
        tool_calls=tool_calls,
    )
    roi = evaluate_automation_roi(
        monthly_frequency=monthly_frequency,
        human_minutes_per_run=human_minutes_per_run,
        human_usd_per_hour=human_usd_per_hour,
        model_usd_per_run=model_usd_per_run,
        review_minutes_per_run=review_minutes_per_run,
        month_to_date_spend_usd=month_to_date_spend_usd,
    )
    trace = summarize_tool_trace(runs=runs)
    ok = (
        platform_d.ok
        and laziness == "ok"
        and completion.ok
        and roi.ok
    )
    return {
        "ok": ok,
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "platform": asdict(platform_d),
        "laziness": laziness,
        "completion": asdict(completion),
        "roi": asdict(roi),
        "trace": asdict(trace),
        "proxy_vs_ground_truth": {
            "note": (
                "completion_rate and cost_per_success_usd are run telemetry proxies; "
                "ledger cash remains separate."
            )
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Agent cost + reliability audit")
    parser.add_argument("--platform", default="local_cost_reliability_audit")
    parser.add_argument("--monthly-frequency", type=int, default=20)
    parser.add_argument("--human-minutes", type=float, default=25.0)
    parser.add_argument("--human-usd-per-hour", type=float, default=50.0)
    parser.add_argument("--model-usd", type=float, default=0.08)
    parser.add_argument("--review-minutes", type=float, default=5.0)
    parser.add_argument("--month-to-date-usd", type=float, default=0.0)
    parser.add_argument("--inspect-json", type=Path, default=None)
    parser.add_argument("--sql", default="SELECT * FROM events LIMIT 20")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.inspect_json is not None:
        result = inspect_json_rows_with_sql(path=args.inspect_json, sql=args.sql)
        payload = asdict(result)
        print(json.dumps(payload, indent=2 if args.json else None, default=str))
        return 0 if result.ok else 2

    roi = evaluate_automation_roi(
        monthly_frequency=args.monthly_frequency,
        human_minutes_per_run=args.human_minutes,
        human_usd_per_hour=args.human_usd_per_hour,
        model_usd_per_run=args.model_usd,
        review_minutes_per_run=args.review_minutes,
        month_to_date_spend_usd=args.month_to_date_usd,
    )
    platform_d = evaluate_platform(platform=args.platform)
    payload = {
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "platform": asdict(platform_d),
        "roi": asdict(roi),
        "ok": platform_d.ok and roi.ok,
    }
    print(json.dumps(payload, indent=2 if args.json else None))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
