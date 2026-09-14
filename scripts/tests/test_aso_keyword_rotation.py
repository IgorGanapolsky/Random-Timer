"""Unit tests for ASO keyword rotation pure helpers."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_ranking_with_feedback_penalizes_zero_installs() -> None:
    from scripts import aso_keyword_rotation as aso

    result = aso.ranking_with_feedback("timer", bid_score=50, posthog_installs={"timer": 0})
    assert result["data_source"] == "posthog"
    assert result["rank"] == 200
    assert result["real_installs"] == 0


def test_ranking_with_feedback_boosts_strong_installs() -> None:
    from scripts import aso_keyword_rotation as aso

    result = aso.ranking_with_feedback(
        "interval timer",
        bid_score=40,
        posthog_installs={"interval timer": 40},
    )
    assert result["data_source"] == "posthog"
    assert result["rank"] == 10
    assert result["impressions_estimate"] == 400


def test_ranking_with_feedback_falls_back_to_simulation() -> None:
    from scripts import aso_keyword_rotation as aso

    result = aso.ranking_with_feedback("unknown kw", bid_score=60, posthog_installs={})
    assert result["data_source"] == "simulated"
    assert result["real_installs"] == -1
    assert "rank" in result
    assert result["rank"] >= 1


def test_select_replacements_skips_ai_trap_and_low_bid() -> None:
    from scripts import aso_keyword_rotation as aso

    backlog = [
        {"keyword": "keep", "bid_score": 90, "ai_trap": False},
        {"keyword": "trap", "bid_score": 99, "ai_trap": True},
        {"keyword": "low", "bid_score": 20, "ai_trap": False},
        {"keyword": "new-a", "bid_score": 80, "ai_trap": False},
        {"keyword": "new-b", "bid_score": 70, "ai_trap": False},
        {"keyword": "new-c", "bid_score": 60, "ai_trap": False},
        {"keyword": "new-d", "bid_score": 55, "ai_trap": False},
    ]
    picked = aso.select_replacements(
        underperforming=[{"keyword": "keep", "rank": 90}],
        current_keywords=["keep"],
        backlog=backlog,
        max_replacements=3,
    )
    assert picked == ["new-a", "new-b", "new-c"]
    assert "trap" not in picked
    assert "low" not in picked


def test_evaluate_keywords_splits_performing_underperforming() -> None:
    from scripts import aso_keyword_rotation as aso

    backlog = [
        {"keyword": "good", "bid_score": 50},
        {"keyword": "bad", "bid_score": 50},
    ]
    result = aso.evaluate_keywords(
        current_keywords=["good", "bad"],
        backlog=backlog,
        target_rank=50,
        posthog_installs={"good": 25, "bad": 0},
    )
    assert [r["keyword"] for r in result["performing"]] == ["good"]
    assert [r["keyword"] for r in result["underperforming"]] == ["bad"]


def test_rotate_ios_keywords_respects_100_char_limit(tmp_path: Path) -> None:
    from scripts import aso_keyword_rotation as aso

    long = ["kw" + str(i) * 20 for i in range(10)]
    out = aso.rotate_ios_keywords(tmp_path, performing=long[:2], replacements=long[2:])
    assert len(out) <= aso.IOS_KEYWORD_LIMIT
    path = tmp_path / aso.IOS_KEYWORDS_PATH
    assert path.read_text(encoding="utf-8").strip() == out


def test_generate_title_variants_respects_play_limit() -> None:
    from scripts import aso_keyword_rotation as aso

    variants = aso.generate_title_variants(
        "Random Tactical Timer",
        ["hiit", "boxing", "a very long keyword that would blow the title limit"],
    )
    assert variants[0] == "Random Tactical Timer"
    assert all(len(v) <= 50 for v in variants)
    assert any("Hiit" in v for v in variants)


def test_build_report_includes_rotation_fields() -> None:
    from scripts import aso_keyword_rotation as aso

    report = aso.build_report(
        {
            "timestamp": "2026-09-14T00:00:00Z",
            "dry_run": True,
            "current_keyword_count": 2,
            "performing": 1,
            "underperforming": 1,
            "removed_keywords": ["b"],
            "replacements_selected": ["c"],
            "new_ios_keywords": "a,c",
            "title_variants": ["Title"],
        }
    )
    assert "Dry Run" in report
    assert "`c`" in report
    assert "a,c" in report
