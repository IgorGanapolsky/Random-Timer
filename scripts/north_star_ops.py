#!/usr/bin/env python3
"""Synthesize a single daily North Star action from growth snapshots."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


ACTIVATION_TARGET = 0.25
STALE_INPUT_HOURS = 48


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _append_staleness_warning(path: Path, warnings: list[str]) -> None:
    if not path.exists():
        warnings.append(f"missing input: {path.relative_to(path.parents[2])}")
        return

    modified = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
    age = dt.datetime.now(dt.timezone.utc) - modified
    if age > dt.timedelta(hours=STALE_INPUT_HOURS):
        warnings.append(
            f"stale input: {path.name} is {int(age.total_seconds() // 3600)}h old"
        )


def _append_quality_warning(path: Path, payload: dict[str, Any], warnings: list[str]) -> None:
    status = str(payload.get("status", "")).strip().lower()
    quality = payload.get("data_quality", {})
    if not isinstance(quality, dict):
        quality = {}
    if status in {"degraded", "skipped"} or quality.get("is_stale"):
        last_good = str(quality.get("last_good_generated_at") or "").strip()
        detail = f"stale metrics in {path.name}"
        if last_good:
            detail += f" (last good `{last_good}`)"
        warnings.append(detail)


def _relative(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve()))


def _activation_experiment(open_to_completed_rate: float) -> dict[str, Any]:
    return {
        "slug": "activation-default-range-0-30",
        "target_metric": "open_to_completed_rate",
        "current_metric_value": round(open_to_completed_rate, 4),
        "target_metric_value": ACTIVATION_TARGET,
        "hypothesis": "Starting every user at 0s to 30s reduces setup friction and increases first completion rate.",
        "owner": "product",
    }


def _retention_experiment(wqtu_7d: int, checkpoint_target: int) -> dict[str, Any]:
    return {
        "slug": "retention-repeat-loop-adoption",
        "target_metric": "WQTU",
        "current_metric_value": wqtu_7d,
        "target_metric_value": checkpoint_target,
        "hypothesis": "Driving repeat-loop adoption increases the number of users completing 3+ timers per week.",
        "owner": "product",
    }


def build_ops_payload(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    data_dir = repo_root / "marketing" / "data"
    north_star_path = data_dir / "north_star.json"
    feedback_path = data_dir / "content_feedback.json"
    cro_path = data_dir / "cro_experiments.json"
    paid_path = data_dir / "paid_campaigns.json"
    apple_ads_path = data_dir / "apple_ads_live_metrics.json"

    north_star_payload = _load_json(north_star_path)
    feedback_payload = _load_json(feedback_path)
    _ = _load_json(cro_path)
    _ = _load_json(paid_path)
    _ = _load_json(apple_ads_path)

    north_star = north_star_payload.get("north_star", {})
    paid = north_star_payload.get("paid", {})
    funnel = feedback_payload.get("onboarding_funnel", {})

    wqtu_7d = int(north_star.get("wqtu_7d", 0) or 0)
    checkpoint_target = int(
        north_star.get("targets", {}).get("checkpoint_2026_03_31", 8) or 8
    )
    open_to_completed_rate = float(funnel.get("open_to_completed_rate", 0.0) or 0.0)

    warnings: list[str] = []
    for path in (north_star_path, feedback_path, cro_path, paid_path, apple_ads_path):
        _append_staleness_warning(path, warnings)
    _append_quality_warning(north_star_path, north_star_payload, warnings)
    _append_quality_warning(feedback_path, feedback_payload, warnings)

    if paid.get("no_scale_lock", {}).get("active"):
        warnings.append("paid no-scale lock is active")

    if open_to_completed_rate < ACTIVATION_TARGET:
        next_experiment = _activation_experiment(open_to_completed_rate)
        target_value = ACTIVATION_TARGET
        current_value = round(open_to_completed_rate, 4)
        gap = round(max(target_value - current_value, 0.0), 4)
        priority_score = max(1, int(gap * 1000) + (25 if wqtu_7d == 0 else 0))
        recommended_next_action = (
            "Ship the default 0s to 30s timer range and verify first-session completion improves."
        )
        primary_focus = "activation"
        primary_metric = "open_to_completed_rate"
    else:
        next_experiment = _retention_experiment(wqtu_7d, checkpoint_target)
        target_value = checkpoint_target
        current_value = wqtu_7d
        gap = max(target_value - current_value, 0)
        priority_score = max(1, int(gap) * 10)
        recommended_next_action = (
            "Increase repeat-loop adoption so more users complete three or more timers per week."
        )
        primary_focus = "retention"
        primary_metric = "WQTU"

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "primary_focus": primary_focus,
        "primary_metric": primary_metric,
        "current_value": current_value,
        "target_value": target_value,
        "gap": gap,
        "priority_score": priority_score,
        "next_experiment": next_experiment,
        "recommended_next_action": recommended_next_action,
        "warnings": warnings,
        "inputs": {
            "north_star": _relative(north_star_path, repo_root),
            "content_feedback": _relative(feedback_path, repo_root),
            "cro_experiments": _relative(cro_path, repo_root),
            "paid_campaigns": _relative(paid_path, repo_root),
            "apple_ads_live_metrics": _relative(apple_ads_path, repo_root),
        },
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    warnings = payload.get("warnings", [])
    warning_lines = "\n".join(f"- {warning}" for warning in warnings) if warnings else "- none"
    experiment = payload["next_experiment"]
    return "\n".join(
        [
            "# North Star Ops",
            "",
            f"- Generated: {payload['generated_at']}",
            f"- Primary Focus: {payload['primary_focus']}",
            f"- Primary Metric: {payload['primary_metric']}",
            f"- Current Value: {payload['current_value']}",
            f"- Target Value: {payload['target_value']}",
            f"- Gap: {payload['gap']}",
            f"- Priority Score: {payload['priority_score']}",
            "",
            "## Next Experiment",
            f"- Slug: {experiment['slug']}",
            f"- Target Metric: {experiment['target_metric']}",
            f"- Current Metric Value: {experiment['current_metric_value']}",
            f"- Target Metric Value: {experiment['target_metric_value']}",
            f"- Hypothesis: {experiment['hypothesis']}",
            f"- Owner: {experiment['owner']}",
            "",
            "## Recommended Next Action",
            payload["recommended_next_action"],
            "",
            "## Warnings",
            warning_lines,
            "",
        ]
    )


def run(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    data_dir = repo_root / "marketing" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    payload = build_ops_payload(repo_root)
    output_json = data_dir / "north_star_ops.json"
    output_markdown = data_dir / "north_star_ops.md"

    output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    output_markdown.write_text(_render_markdown(payload), encoding="utf-8")

    return {
        "status": "ok",
        "output_json": str(output_json),
        "output_markdown": str(output_markdown),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the daily North Star ops report.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run(Path(args.repo_root))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
