from __future__ import annotations

import json
from pathlib import Path

from scripts import north_star_experiment as nse


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_build_experiment_brief_uses_activation_plan(tmp_path: Path):
    repo_root = tmp_path
    _write_json(
        repo_root / "marketing/data/north_star_ops.json",
        {
            "generated_at": "2026-03-09T18:00:00+00:00",
            "primary_focus": "activation",
            "primary_metric": "open_to_completed_rate",
            "current_value": 0.12,
            "target_value": 0.25,
            "gap": 0.13,
            "recommended_next_action": "Ship the default 0s to 30s timer range.",
            "next_experiment": {
                "slug": "activation-default-range-0-30",
                "target_metric": "open_to_completed_rate",
                "current_metric_value": 0.12,
                "target_metric_value": 0.25,
                "hypothesis": "Lower setup friction improves first completion.",
                "owner": "product",
            },
            "warnings": [],
        },
    )

    payload = nse.build_experiment_brief(repo_root)

    assert payload["primary_focus"] == "activation"
    assert payload["measurement_plan"]["window_days"] == 30
    assert any("0s to 30s" in item for item in payload["implementation_checklist"])


def test_build_experiment_brief_uses_retention_plan(tmp_path: Path):
    repo_root = tmp_path
    _write_json(
        repo_root / "marketing/data/north_star_ops.json",
        {
            "generated_at": "2026-03-09T18:00:00+00:00",
            "primary_focus": "retention",
            "primary_metric": "WQTU",
            "current_value": 2,
            "target_value": 8,
            "gap": 6,
            "recommended_next_action": "Increase repeat-loop adoption.",
            "next_experiment": {
                "slug": "retention-repeat-loop-adoption",
                "target_metric": "WQTU",
                "current_metric_value": 2,
                "target_metric_value": 8,
                "hypothesis": "Loop adoption improves repeat weekly completions.",
                "owner": "product",
            },
            "warnings": ["paid no-scale lock is active"],
        },
    )

    payload = nse.build_experiment_brief(repo_root)

    assert payload["primary_focus"] == "retention"
    assert payload["measurement_plan"]["window_days"] == 7
    assert any("repeat-loop" in item for item in payload["implementation_checklist"])
    assert payload["warnings"] == ["paid no-scale lock is active"]


def test_run_writes_json_and_markdown_reports(tmp_path: Path):
    repo_root = tmp_path
    _write_json(
        repo_root / "marketing/data/north_star_ops.json",
        {
            "generated_at": "2026-03-09T18:00:00+00:00",
            "primary_focus": "activation",
            "primary_metric": "open_to_completed_rate",
            "current_value": 0.12,
            "target_value": 0.25,
            "gap": 0.13,
            "recommended_next_action": "Ship the default 0s to 30s timer range.",
            "next_experiment": {
                "slug": "activation-default-range-0-30",
                "target_metric": "open_to_completed_rate",
                "current_metric_value": 0.12,
                "target_metric_value": 0.25,
                "hypothesis": "Lower setup friction improves first completion.",
                "owner": "product",
            },
            "warnings": [],
        },
    )

    result = nse.run(repo_root)

    json_path = repo_root / "marketing/data/north_star_experiment.json"
    md_path = repo_root / "marketing/data/north_star_experiment.md"
    assert result["output_json"] == str(json_path)
    assert result["output_markdown"] == str(md_path)
    assert json_path.exists()
    assert md_path.exists()
    assert "North Star Experiment" in md_path.read_text(encoding="utf-8")
