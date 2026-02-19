#!/usr/bin/env python3
"""Policy router for App Store review operations.

Consumes:
  - current reviews report (asc_reviews_ops JSON)
  - anomaly detector report (review_anomaly_detector JSON)

Produces:
  - deterministic action policy JSON + optional markdown
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROUTES = {"MONITOR", "AUTO_RESPOND_TEMPLATE", "ESCALATE_HUMAN"}


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _severity_rank(value: str) -> int:
    order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    return order.get(str(value), 0)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_io_path(raw_path: str, cwd: Path) -> Path:
    candidate = Path(raw_path).expanduser().resolve()
    allowed_roots = {
        cwd.resolve(),
        Path("/tmp").resolve(),
        Path(tempfile.gettempdir()).resolve(),
    }
    if any(_is_within(candidate, root) for root in allowed_roots):
        return candidate
    allowed_str = ", ".join(sorted(str(r) for r in allowed_roots))
    raise ValueError(f"Path outside allowed roots ({allowed_str}): {candidate}")


def _top_breaches(reviews_report: Dict[str, Any], max_items: int = 10) -> List[Dict[str, Any]]:
    rows = list(reviews_report.get("slaBreaches", []) or [])
    rows.sort(key=lambda r: float(r.get("ageHours") or 0.0), reverse=True)
    return rows[:max_items]


def evaluate_policy(
    *,
    mode: str,
    reviews_report: Dict[str, Any],
    anomaly_report: Dict[str, Any],
) -> Dict[str, Any]:
    if mode not in {"observe", "enforce"}:
        raise ValueError(f"Invalid mode: {mode}")

    sla_breach_count = _as_int(reviews_report.get("slaBreachCount"))
    unresolved_low = _as_int(reviews_report.get("unresolvedLowStarCount"))
    avg_rating = _as_float(reviews_report.get("averageRating"))

    anomaly_status = str(anomaly_report.get("status") or "unknown")
    max_severity = str(anomaly_report.get("maxSeverity") or "none")
    anomaly_score = _as_int(anomaly_report.get("score"))

    route = "MONITOR"
    blocking = False
    reasons: List[str] = []
    actions: List[Dict[str, Any]] = []

    if sla_breach_count > 0:
        route = "ESCALATE_HUMAN"
        reasons.append("SLA breaches present for unresolved low-star reviews.")
        actions.append(
            {
                "type": "OPEN_RESPONSE_WAR_ROOM",
                "priority": "p1",
                "evidence": {"slaBreachCount": sla_breach_count, "topBreaches": _top_breaches(reviews_report, 10)},
            }
        )
        actions.append(
            {
                "type": "POST_TEAM_ALERT",
                "priority": "p1",
                "evidence": {"channel": "slack", "summary": "Unresolved low-star SLA breaches detected."},
            }
        )

    if _severity_rank(max_severity) >= _severity_rank("high") or anomaly_status == "alert":
        route = "ESCALATE_HUMAN"
        reasons.append("High-severity anomaly detected in review trend.")
        actions.append(
            {
                "type": "CREATE_INCIDENT_TASK",
                "priority": "p1" if _severity_rank(max_severity) >= _severity_rank("critical") else "p2",
                "evidence": {
                    "anomalyStatus": anomaly_status,
                    "maxSeverity": max_severity,
                    "score": anomaly_score,
                    "anomalies": anomaly_report.get("anomalies", []),
                },
            }
        )

    if route == "MONITOR" and unresolved_low > 0:
        route = "AUTO_RESPOND_TEMPLATE"
        reasons.append("Unresolved low-star reviews exist but no severe trend anomaly.")
        actions.append(
            {
                "type": "QUEUE_TEMPLATE_RESPONSES",
                "priority": "p2",
                "evidence": {"unresolvedLowStarCount": unresolved_low},
            }
        )

    if route == "MONITOR":
        reasons.append("No severe anomalies or SLA breaches. Continue periodic monitoring.")
        actions.append(
            {
                "type": "NOOP_MONITOR_ONLY",
                "priority": "p3",
                "evidence": {"averageRating": avg_rating},
            }
        )

    if mode == "enforce" and route == "ESCALATE_HUMAN":
        blocking = True
    if mode == "enforce" and route == "AUTO_RESPOND_TEMPLATE" and unresolved_low >= 10:
        blocking = True
        reasons.append("Enforce mode: unresolved queue size exceeds hard threshold.")

    decision = {
        "route": route,
        "blocking": blocking,
        "reasoning": reasons,
    }

    if route not in ROUTES:
        raise RuntimeError(f"Unexpected route: {route}")

    return {
        "generatedAt": _iso_now(),
        "mode": mode,
        "policyVersion": "2026-02-19",
        "anomalyStatus": anomaly_status,
        "maxSeverity": max_severity,
        "score": anomaly_score,
        "inputs": {
            "slaBreachCount": sla_breach_count,
            "unresolvedLowStarCount": unresolved_low,
            "averageRating": avg_rating,
            "totalReviews": _as_int(reviews_report.get("totalReviews")),
        },
        "decision": decision,
        "actions": actions,
    }


def _render_markdown(policy: Dict[str, Any]) -> str:
    decision = policy.get("decision", {}) or {}
    lines: List[str] = []
    lines.append("# ASC Review Action Policy")
    lines.append("")
    lines.append(f"- Generated: {policy.get('generatedAt')}")
    lines.append(f"- Mode: `{policy.get('mode')}`")
    lines.append(f"- Route: **{decision.get('route')}**")
    lines.append(f"- Blocking: `{decision.get('blocking')}`")
    lines.append(f"- Anomaly status: `{policy.get('anomalyStatus')}`")
    lines.append(f"- Max severity: `{policy.get('maxSeverity')}`")
    lines.append("")
    lines.append("## Reasoning")
    lines.append("")
    for r in decision.get("reasoning", []) or []:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("## Actions")
    lines.append("")
    actions = policy.get("actions", []) or []
    if not actions:
        lines.append("- none")
    else:
        for action in actions:
            lines.append(f"- `{action.get('type')}` ({action.get('priority')})")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Apply deterministic policy to review + anomaly reports.")
    p.add_argument("--reviews-json", required=True)
    p.add_argument("--anomaly-json", required=True)
    p.add_argument("--mode", choices=["observe", "enforce"], default="observe")
    p.add_argument("--json-out", required=True)
    p.add_argument("--markdown-out")
    p.add_argument("--fail-on-blocking", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path.cwd().resolve()
    reviews_path = _safe_io_path(args.reviews_json, cwd)
    anomaly_path = _safe_io_path(args.anomaly_json, cwd)
    out_path = _safe_io_path(args.json_out, cwd)

    reviews_report = json.loads(reviews_path.read_text(encoding="utf-8"))
    anomaly_report = json.loads(anomaly_path.read_text(encoding="utf-8"))

    policy = evaluate_policy(mode=args.mode, reviews_report=reviews_report, anomaly_report=anomaly_report)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(policy, ensure_ascii=True, indent=2), encoding="utf-8")  # NOSONAR

    if args.markdown_out:
        md_path = _safe_io_path(args.markdown_out, cwd)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(_render_markdown(policy), encoding="utf-8")  # NOSONAR

    decision = policy.get("decision", {}) or {}
    print("══ Review Action Policy ═══════════════════════════")
    print(f"Mode:        {policy.get('mode')}")
    print(f"Route:       {decision.get('route')}")
    print(f"Blocking:    {decision.get('blocking')}")
    print(f"Output:      {out_path}")
    print("═══════════════════════════════════════════════════")

    if args.fail_on_blocking and bool(decision.get("blocking")):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
