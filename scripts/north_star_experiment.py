#!/usr/bin/env python3
"""Generate a single weekly experiment brief tied to the North Star gap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts import north_star_ops


def _load_ops_payload(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "marketing" / "data" / "north_star_ops.json"
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        if isinstance(payload, dict) and payload.get("next_experiment"):
            return payload
    return north_star_ops.build_ops_payload(repo_root)


def _measurement_window_days(primary_metric: str) -> int:
    return 30 if primary_metric == "open_to_completed_rate" else 7


def _implementation_checklist(primary_focus: str) -> list[str]:
    if primary_focus == "activation":
        return [
            "Keep launch defaults at 0s to 30s on both platforms.",
            "Keep setup-screen previews visible for countdown and drill voice cues.",
            "Verify first-session setup and start flow with smoke evidence on iOS and Android.",
        ]
    return [
        "Promote repeat-loop usage without degrading the default first-session flow.",
        "Track repeat usage behavior with existing timer analytics parity.",
        "Verify loop and stop behavior with mobile tests before merge.",
    ]


def build_experiment_brief(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    ops = _load_ops_payload(repo_root)
    experiment = ops["next_experiment"]
    primary_metric = str(ops["primary_metric"])

    return {
        "generated_at": ops["generated_at"],
        "status": "proposed",
        "primary_focus": ops["primary_focus"],
        "recommended_next_action": ops["recommended_next_action"],
        "experiment": experiment,
        "measurement_plan": {
            "metric": primary_metric,
            "baseline": ops["current_value"],
            "target": ops["target_value"],
            "gap": ops["gap"],
            "window_days": _measurement_window_days(primary_metric),
        },
        "implementation_checklist": _implementation_checklist(str(ops["primary_focus"])),
        "proof_commands": [
            "python3 -m pytest -q scripts/tests/",
            "cd native-android && ./gradlew testDebugUnitTest",
            "cd native-ios && xcodebuild test -project RandomTimer.xcodeproj -scheme RandomTimer -destination 'platform=iOS Simulator,id=<SIMULATOR_ID>' -skip-testing:RandomTimerUITests -quiet CODE_SIGNING_ALLOWED=NO",
        ],
        "warnings": ops.get("warnings", []),
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    experiment = payload["experiment"]
    measurement = payload["measurement_plan"]
    checklist = "\n".join(f"- {item}" for item in payload["implementation_checklist"])
    proof = "\n".join(f"- `{item}`" for item in payload["proof_commands"])
    warnings = payload.get("warnings", [])
    warning_lines = "\n".join(f"- {item}" for item in warnings) if warnings else "- none"
    return "\n".join(
        [
            "# North Star Experiment",
            "",
            f"- Generated: {payload['generated_at']}",
            f"- Status: {payload['status']}",
            f"- Primary Focus: {payload['primary_focus']}",
            "",
            "## Experiment",
            f"- Slug: {experiment['slug']}",
            f"- Target Metric: {experiment['target_metric']}",
            f"- Hypothesis: {experiment['hypothesis']}",
            f"- Owner: {experiment['owner']}",
            "",
            "## Measurement Plan",
            f"- Metric: {measurement['metric']}",
            f"- Baseline: {measurement['baseline']}",
            f"- Target: {measurement['target']}",
            f"- Gap: {measurement['gap']}",
            f"- Window Days: {measurement['window_days']}",
            "",
            "## Recommended Next Action",
            payload["recommended_next_action"],
            "",
            "## Implementation Checklist",
            checklist,
            "",
            "## Proof Commands",
            proof,
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

    payload = build_experiment_brief(repo_root)
    output_json = data_dir / "north_star_experiment.json"
    output_markdown = data_dir / "north_star_experiment.md"

    output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    output_markdown.write_text(_render_markdown(payload), encoding="utf-8")

    return {
        "status": "ok",
        "output_json": str(output_json),
        "output_markdown": str(output_markdown),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the weekly North Star experiment brief.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run(Path(args.repo_root))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
