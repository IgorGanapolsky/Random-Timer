from __future__ import annotations

import json
from pathlib import Path

from scripts import north_star_ops as nso


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_build_ops_payload_prioritizes_activation_when_completion_is_low(tmp_path: Path):
    repo_root = tmp_path
    _write_json(
        repo_root / "marketing/data/north_star.json",
        {
            "north_star": {
                "wqtu_7d": 0,
                "targets": {"checkpoint_2026_03_31": 8, "quarter_2026_06_30": 25},
            },
            "paid": {"paid_distinct_users_30d": 0, "no_scale_lock": {"active": False, "reasons": []}},
        },
    )
    _write_json(
        repo_root / "marketing/data/content_feedback.json",
        {
            "onboarding_funnel": {
                "first_open": 87,
                "first_timer_configured": 71,
                "first_timer_completed": 2,
                "open_to_configured_rate": 0.8161,
                "configured_to_completed_rate": 0.0282,
                "open_to_completed_rate": 0.023,
                "window_days": 30,
            },
            "top_campaigns_by_activation": [],
        },
    )

    payload = nso.build_ops_payload(repo_root)

    assert payload["primary_focus"] == "activation"
    assert payload["next_experiment"]["slug"] == "activation-default-range-0-30"
    assert payload["next_experiment"]["target_metric"] == "open_to_completed_rate"
    assert payload["priority_score"] > 0
    assert payload["inputs"]["north_star"] == "marketing/data/north_star.json"
    assert payload["inputs"]["content_feedback"] == "marketing/data/content_feedback.json"


def test_build_ops_payload_prioritizes_retention_when_activation_is_healthy(tmp_path: Path):
    repo_root = tmp_path
    _write_json(
        repo_root / "marketing/data/north_star.json",
        {
            "north_star": {
                "wqtu_7d": 1,
                "targets": {"checkpoint_2026_03_31": 8, "quarter_2026_06_30": 25},
            },
            "paid": {"paid_distinct_users_30d": 3, "no_scale_lock": {"active": False, "reasons": []}},
        },
    )
    _write_json(
        repo_root / "marketing/data/content_feedback.json",
        {
            "onboarding_funnel": {
                "first_open": 100,
                "first_timer_configured": 80,
                "first_timer_completed": 30,
                "open_to_configured_rate": 0.8,
                "configured_to_completed_rate": 0.375,
                "open_to_completed_rate": 0.3,
                "window_days": 30,
            },
            "top_campaigns_by_activation": [{"campaign": "asa_brand", "activated_users": 4}],
        },
    )

    payload = nso.build_ops_payload(repo_root)

    assert payload["primary_focus"] == "retention"
    assert payload["next_experiment"]["slug"] == "retention-repeat-loop-adoption"
    assert payload["next_experiment"]["target_metric"] == "WQTU"


def test_run_writes_json_and_markdown_reports(tmp_path: Path):
    repo_root = tmp_path
    _write_json(
        repo_root / "marketing/data/north_star.json",
        {
            "north_star": {
                "wqtu_7d": 0,
                "targets": {"checkpoint_2026_03_31": 8, "quarter_2026_06_30": 25},
            },
            "paid": {"paid_distinct_users_30d": 0, "no_scale_lock": {"active": False, "reasons": []}},
        },
    )
    _write_json(
        repo_root / "marketing/data/content_feedback.json",
        {
            "onboarding_funnel": {
                "first_open": 10,
                "first_timer_configured": 8,
                "first_timer_completed": 1,
                "open_to_configured_rate": 0.8,
                "configured_to_completed_rate": 0.125,
                "open_to_completed_rate": 0.1,
                "window_days": 30,
            },
            "top_campaigns_by_activation": [],
        },
    )

    result = nso.run(repo_root)

    json_path = repo_root / "marketing/data/north_star_ops.json"
    md_path = repo_root / "marketing/data/north_star_ops.md"
    assert result["output_json"] == str(json_path)
    assert result["output_markdown"] == str(md_path)
    assert json_path.exists()
    assert md_path.exists()
    assert "Next Experiment" in md_path.read_text(encoding="utf-8")
