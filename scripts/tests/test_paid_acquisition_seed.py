from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_paid_campaigns(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "campaigns": [
            {
                "platform": "apple_search_ads",
                "status": "active",
                "campaign_id": 12345,
                "launched_at": "2026-02-24T16:30:00Z",
                "daily_budget_usd": 10.0,
            },
            {
                "platform": "google_uac",
                "status": "ready_to_launch",
                "daily_budget_usd": 10.0,
            },
            {
                "platform": "reddit_ads",
                "status": "ready_to_launch",
                "daily_budget_usd": 10.0,
            },
        ],
        "budget_config": {
            "daily_budget_usd": 30.0,
            "launch_week_multiplier": 1.5,
            "max_cpt_usd": 1.5,
            "target_cpa_usd": 3.0,
        },
        "history": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _sample_backlog() -> list[dict[str, object]]:
    return [
        {"keyword": "random timer", "bid_score": 80, "ai_trap": False, "intent": "commercial"},
        {"keyword": "interval timer", "bid_score": 62, "ai_trap": False, "intent": "tool"},
        {"keyword": "boxing drills", "bid_score": 54, "ai_trap": False, "intent": "tool"},
        {"keyword": "fitness timer", "bid_score": 48, "ai_trap": False, "intent": "commercial"},
    ]


def test_run_acquisition_preserves_unmanaged_campaigns_and_caps_budget(monkeypatch, tmp_path):
    from scripts import paid_acquisition_seed as pas

    _write_paid_campaigns(tmp_path / "marketing" / "data" / "paid_campaigns.json")
    monkeypatch.setattr(pas, "load_blueprint", lambda _p: {})
    monkeypatch.setattr(pas, "build_backlog", lambda _b: _sample_backlog())

    result = pas.run_acquisition(
        tmp_path,
        budget_override={**pas.DEFAULT_BUDGET, "daily_budget_usd": 100.0},
    )
    assert result["budget"]["daily_budget_usd"] == pytest.approx(35.0)

    persisted = json.loads((tmp_path / "marketing" / "data" / "paid_campaigns.json").read_text(encoding="utf-8"))
    campaigns = {item["platform"]: item for item in persisted["campaigns"]}
    assert set(campaigns.keys()) == {"apple_search_ads", "google_uac", "reddit_ads"}
    assert campaigns["apple_search_ads"]["status"] == "active"
    assert campaigns["apple_search_ads"]["campaign_id"] == 12345
    assert campaigns["apple_search_ads"]["launched_at"] == "2026-02-24T16:30:00Z"
    assert campaigns["reddit_ads"]["status"] == "ready_to_launch"

    history = persisted["history"][-1]
    assert history["action"] == "campaign_refresh"
    assert history["daily_budget_requested_usd"] == pytest.approx(100.0)
    assert history["daily_budget_applied_usd"] == pytest.approx(35.0)
    assert history["budget_capped"] is True
