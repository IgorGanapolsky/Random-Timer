#!/usr/bin/env python3
"""Detect anomalies in App Store review operations metrics.

Input shape is the JSON emitted by scripts/asc/asc_reviews_ops.py.
The detector is deterministic and explainable:
  - robust baseline from median + MAD over history
  - explicit absolute floors for each metric
  - machine-readable evidence in output JSON
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso(value: str) -> Optional[dt.datetime]:
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


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


def extract_metrics(report: Dict[str, Any]) -> Dict[str, float]:
    ratings = report.get("ratings", {}) or {}
    r1 = _as_int(ratings.get("1"))
    r2 = _as_int(ratings.get("2"))
    r3 = _as_int(ratings.get("3"))
    total = max(1, _as_int(report.get("totalReviews")))

    low_star_rate = (r1 + r2 + r3) / float(total)
    return {
        "average_rating": _as_float(report.get("averageRating")),
        "low_star_rate": low_star_rate,
        "unresolved_low_star_count": float(_as_int(report.get("unresolvedLowStarCount"))),
        "sla_breach_count": float(_as_int(report.get("slaBreachCount"))),
        "total_reviews": float(_as_int(report.get("totalReviews"))),
    }


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.median(values))


def _mad(values: List[float], med: float) -> float:
    if not values:
        return 0.0
    deviations = [abs(v - med) for v in values]
    return float(statistics.median(deviations))


def _robust_sigma(values: List[float], med: float) -> float:
    mad = _mad(values, med)
    if mad > 0:
        return 1.4826 * mad
    if len(values) >= 2:
        try:
            stdev = statistics.pstdev(values)
            if stdev > 0:
                return float(stdev)
        except statistics.StatisticsError:
            pass
    return max(0.05, abs(med) * 0.05)


def _severity(delta: float, threshold: float) -> str:
    if threshold <= 0:
        return "medium"
    ratio = abs(delta) / threshold
    if ratio >= 2.0:
        return "critical"
    if ratio >= 1.5:
        return "high"
    if ratio >= 1.0:
        return "medium"
    return "low"


def _append_anomaly(
    anomalies: List[Dict[str, Any]],
    *,
    metric: str,
    direction: str,
    current: float,
    baseline: float,
    threshold: float,
    reason: str,
) -> None:
    delta = current - baseline
    anomalies.append(
        {
            "metric": metric,
            "direction": direction,
            "current": round(current, 6),
            "baselineMedian": round(baseline, 6),
            "delta": round(delta, 6),
            "threshold": round(threshold, 6),
            "severity": _severity(delta, threshold),
            "reason": reason,
        }
    )


def load_history(
    path: Path,
    *,
    current_generated_at: Optional[str],
    max_age_days: int,
) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []

    now = dt.datetime.now(dt.timezone.utc)
    current_ts = _parse_iso(current_generated_at or "")
    rows: List[Dict[str, Any]] = []
    seen_keys: set[str] = set()

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue

        generated_at = str(item.get("generatedAt") or "")
        parsed = _parse_iso(generated_at)
        if parsed is None:
            continue
        age_days = (now - parsed).total_seconds() / 86400.0
        if max_age_days > 0 and age_days > max_age_days:
            continue
        if current_ts and parsed >= current_ts:
            continue

        dedupe_key = "|".join(
            [
                generated_at,
                str(item.get("totalReviews")),
                str(item.get("averageRating")),
                str(item.get("unresolvedLowStarCount")),
                str(item.get("slaBreachCount")),
            ]
        )
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        rows.append(item)

    rows.sort(key=lambda r: str(r.get("generatedAt") or ""))
    return rows


def detect_anomalies(
    *,
    current_report: Dict[str, Any],
    history_reports: List[Dict[str, Any]],
    min_history: int,
    rating_drop_threshold: float,
    low_star_rate_spike_threshold: float,
    unresolved_spike_threshold: float,
    sla_breach_spike_threshold: float,
) -> Dict[str, Any]:
    current_metrics = extract_metrics(current_report)
    baseline_series: Dict[str, List[float]] = {
        "average_rating": [],
        "low_star_rate": [],
        "unresolved_low_star_count": [],
        "sla_breach_count": [],
        "total_reviews": [],
    }
    for hist in history_reports:
        m = extract_metrics(hist)
        for key in baseline_series:
            baseline_series[key].append(m[key])

    baseline: Dict[str, Dict[str, float]] = {}
    for key, values in baseline_series.items():
        med = _median(values)
        sigma = _robust_sigma(values, med) if values else 0.0
        baseline[key] = {
            "median": round(med, 6),
            "sigma": round(sigma, 6),
            "count": len(values),
        }

    anomalies: List[Dict[str, Any]] = []
    has_history = len(history_reports) >= min_history

    if has_history:
        avg_base = baseline["average_rating"]["median"]
        avg_sigma = baseline["average_rating"]["sigma"]
        avg_threshold = max(float(rating_drop_threshold), 3.0 * avg_sigma)
        if current_metrics["average_rating"] < avg_base - avg_threshold:
            _append_anomaly(
                anomalies,
                metric="average_rating",
                direction="drop",
                current=current_metrics["average_rating"],
                baseline=avg_base,
                threshold=avg_threshold,
                reason="Average rating dropped below robust baseline.",
            )

        low_star_base = baseline["low_star_rate"]["median"]
        low_star_sigma = baseline["low_star_rate"]["sigma"]
        low_star_threshold = max(float(low_star_rate_spike_threshold), 3.0 * low_star_sigma)
        if current_metrics["low_star_rate"] > low_star_base + low_star_threshold:
            _append_anomaly(
                anomalies,
                metric="low_star_rate",
                direction="spike",
                current=current_metrics["low_star_rate"],
                baseline=low_star_base,
                threshold=low_star_threshold,
                reason="1-3 star share spiked above robust baseline.",
            )

        unresolved_base = baseline["unresolved_low_star_count"]["median"]
        unresolved_sigma = baseline["unresolved_low_star_count"]["sigma"]
        unresolved_threshold = max(float(unresolved_spike_threshold), 3.0 * unresolved_sigma)
        if current_metrics["unresolved_low_star_count"] > unresolved_base + unresolved_threshold:
            _append_anomaly(
                anomalies,
                metric="unresolved_low_star_count",
                direction="spike",
                current=current_metrics["unresolved_low_star_count"],
                baseline=unresolved_base,
                threshold=unresolved_threshold,
                reason="Unresolved low-star queue spiked above robust baseline.",
            )

        sla_base = baseline["sla_breach_count"]["median"]
        sla_sigma = baseline["sla_breach_count"]["sigma"]
        sla_threshold = max(float(sla_breach_spike_threshold), 3.0 * sla_sigma)
        if current_metrics["sla_breach_count"] > sla_base + sla_threshold:
            _append_anomaly(
                anomalies,
                metric="sla_breach_count",
                direction="spike",
                current=current_metrics["sla_breach_count"],
                baseline=sla_base,
                threshold=sla_threshold,
                reason="SLA breach count spiked above robust baseline.",
            )

    # Guardrail anomaly independent of baseline.
    if current_metrics["sla_breach_count"] > 0:
        _append_anomaly(
            anomalies,
            metric="sla_breach_count",
            direction="present",
            current=current_metrics["sla_breach_count"],
            baseline=0.0,
            threshold=1.0,
            reason="At least one SLA breach is currently unresolved.",
        )

    severity_weight = {"low": 1, "medium": 3, "high": 6, "critical": 10}
    score = int(sum(severity_weight.get(a.get("severity", "low"), 1) for a in anomalies))
    max_severity = "none"
    if anomalies:
        ordered = ["none", "low", "medium", "high", "critical"]
        max_severity = max(anomalies, key=lambda a: ordered.index(a["severity"]))["severity"]

    if max_severity in ("high", "critical"):
        status = "alert"
    elif anomalies:
        status = "warn"
    elif not has_history:
        status = "observe"
    else:
        status = "ok"

    return {
        "generatedAt": _iso_now(),
        "status": status,
        "maxSeverity": max_severity,
        "score": score,
        "historyCount": len(history_reports),
        "minHistory": min_history,
        "insufficientHistory": not has_history,
        "currentMetrics": {k: round(v, 6) for k, v in current_metrics.items()},
        "baseline": baseline,
        "anomalies": anomalies,
    }


def _render_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# ASC Review Anomaly Report")
    lines.append("")
    lines.append(f"- Generated: {payload['generatedAt']}")
    lines.append(f"- Status: **{payload['status']}**")
    lines.append(f"- Max severity: `{payload['maxSeverity']}`")
    lines.append(f"- Score: {payload['score']}")
    lines.append(f"- History samples: {payload['historyCount']}")
    lines.append("")
    lines.append("## Current Metrics")
    lines.append("")
    for key, value in payload.get("currentMetrics", {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Anomalies")
    lines.append("")
    anomalies = payload.get("anomalies", []) or []
    if not anomalies:
        lines.append("- none")
    else:
        lines.append("| Metric | Direction | Severity | Current | Baseline | Threshold |")
        lines.append("|---|---|---|---:|---:|---:|")
        for row in anomalies:
            lines.append(
                f"| {row['metric']} | {row['direction']} | {row['severity']} | "
                f"{row['current']} | {row['baselineMedian']} | {row['threshold']} |"
            )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Detect App Store reviews anomalies from historical snapshots.")
    p.add_argument("--current-json", required=True, help="Current asc_reviews_ops JSON report")
    p.add_argument("--history-jsonl", help="Historical reports JSONL (one asc_reviews_ops report per line)")
    p.add_argument("--json-out", required=True, help="Output anomaly JSON path")
    p.add_argument("--markdown-out", help="Optional markdown output path")
    p.add_argument("--min-history", type=int, default=8, help="Minimum history points for robust baseline")
    p.add_argument("--max-age-days", type=int, default=30, help="Ignore history older than N days (default 30)")
    p.add_argument("--rating-drop-threshold", type=float, default=0.25)
    p.add_argument("--low-star-rate-spike-threshold", type=float, default=0.05)
    p.add_argument("--unresolved-spike-threshold", type=float, default=3.0)
    p.add_argument("--sla-breach-spike-threshold", type=float, default=1.0)
    p.add_argument("--fail-on-alert", action="store_true", help="Return exit 1 when status=alert")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    current_path = Path(args.current_json).resolve()
    history_path = Path(args.history_jsonl).resolve() if args.history_jsonl else None
    out_path = Path(args.json_out).resolve()

    current_report = json.loads(current_path.read_text(encoding="utf-8"))
    history_reports = (
        load_history(
            history_path,
            current_generated_at=str(current_report.get("generatedAt") or ""),
            max_age_days=max(0, int(args.max_age_days)),
        )
        if history_path
        else []
    )

    payload = detect_anomalies(
        current_report=current_report,
        history_reports=history_reports,
        min_history=max(1, int(args.min_history)),
        rating_drop_threshold=float(args.rating_drop_threshold),
        low_star_rate_spike_threshold=float(args.low_star_rate_spike_threshold),
        unresolved_spike_threshold=float(args.unresolved_spike_threshold),
        sla_breach_spike_threshold=float(args.sla_breach_spike_threshold),
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    if args.markdown_out:
        md_path = Path(args.markdown_out).resolve()
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(_render_markdown(payload), encoding="utf-8")

    print("══ Review Anomaly Detector ════════════════════════")
    print(f"Current report:   {current_path}")
    print(f"History points:   {payload['historyCount']}")
    print(f"Status:           {payload['status']}")
    print(f"Max severity:     {payload['maxSeverity']}")
    print(f"Score:            {payload['score']}")
    print(f"Anomalies:        {len(payload.get('anomalies', []))}")
    print(f"Output:           {out_path}")
    print("═══════════════════════════════════════════════════")

    if args.fail_on_alert and payload.get("status") == "alert":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
