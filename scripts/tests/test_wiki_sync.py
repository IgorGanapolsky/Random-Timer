"""Tests for wiki_sync.py — dashboard data injection."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wiki_sync import inject_dashboard_data, load_json, load_jsonl


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Create a temporary marketing/data directory with sample JSON files."""
    d = tmp_path / "data"
    d.mkdir()

    # review_velocity.json
    (d / "review_velocity.json").write_text(json.dumps({
        "snapshots": [{
            "timestamp": "2026-02-20T00:00:00+00:00",
            "ios_total": 42,
            "ios_rating": 4.5,
            "ios_recent_7d": 7,
            "android_total": 30,
            "android_rating": 4.2,
            "android_recent_7d": 5,
        }],
        "alerts": [],
        "latest_velocity": {"ios_velocity": 1.0, "android_velocity": 0.71},
        "review_prompt_config": {
            "completions_before_prompt": 3,
            "min_days_between_prompts": 30,
            "prompt_after_positive_experience": True,
            "suppress_during_low_rating_period": True,
        },
    }))

    # cro_experiments.json
    (d / "cro_experiments.json").write_text(json.dumps([
        {"type": "title_ab_test", "platform": "android", "status": "active", "duration_days": 14},
        {"type": "screenshot_ab", "platform": "both", "status": "proposed", "duration_days": 21},
    ]))

    # paid_campaigns.json
    (d / "paid_campaigns.json").write_text(json.dumps({
        "campaigns": [
            {
                "platform": "apple_search_ads",
                "status": "draft",
                "ad_groups": [{"keywords": [{"text": "kw1"}, {"text": "kw2"}]}],
            },
            {
                "platform": "google_uac",
                "status": "draft",
                "ad_groups": [],
                "targeting": {"keyword_themes": ["hiit", "timer"]},
            },
        ],
        "budget_allocation": {"apple_search_ads": 6.0, "google_uac": 4.0},
    }))

    # posts.jsonl
    (d / "posts.jsonl").write_text(
        json.dumps({"title": "Test Post", "timestamp": "2026-02-20T12:00:00+00:00"}) + "\n"
    )

    # referral_campaigns.json
    (d / "referral_campaigns.json").write_text(json.dumps({
        "campaigns": [],
        "reddit_posts": [
            {"id": "1", "subreddit": "r/HIIT", "status": "draft"},
            {"id": "2", "subreddit": "r/boxing", "status": "draft"},
        ],
        "product_hunt": {"status": "draft"},
        "blog_outreach": [
            {"target": "fitness", "status": "draft"},
        ],
    }))

    return d


@pytest.fixture
def dashboard_template() -> str:
    return textwrap.dedent("""\
        # Dashboard

        <!-- REVIEWS_START -->
        placeholder
        <!-- REVIEWS_END -->

        <!-- CRO_START -->
        placeholder
        <!-- CRO_END -->

        <!-- CAMPAIGNS_START -->
        placeholder
        <!-- CAMPAIGNS_END -->

        <!-- CONTENT_START -->
        placeholder
        <!-- CONTENT_END -->

        <!-- REFERRAL_START -->
        placeholder
        <!-- REFERRAL_END -->

        <!-- TIMESTAMP -->
    """)


def test_inject_reviews(data_dir: Path, dashboard_template: str) -> None:
    result = inject_dashboard_data(dashboard_template, data_dir)
    assert "42" in result  # ios_total
    assert "4.5" in result  # ios_rating
    assert "1.0 reviews/day" in result
    assert "Show after 3 completions" in result


def test_inject_cro(data_dir: Path, dashboard_template: str) -> None:
    result = inject_dashboard_data(dashboard_template, data_dir)
    assert "title_ab_test" in result
    assert "active" in result
    assert "14 days" in result


def test_inject_campaigns(data_dir: Path, dashboard_template: str) -> None:
    result = inject_dashboard_data(dashboard_template, data_dir)
    assert "$6.00" in result
    assert "$4.00" in result
    assert "$10.00" in result
    assert "apple_search_ads" in result


def test_inject_content(data_dir: Path, dashboard_template: str) -> None:
    result = inject_dashboard_data(dashboard_template, data_dir)
    assert "Test Post" in result
    assert "Total Posts Published | 1" in result


def test_inject_referral(data_dir: Path, dashboard_template: str) -> None:
    result = inject_dashboard_data(dashboard_template, data_dir)
    assert "Reddit Posts | 2" in result
    assert "Product Hunt | 1" in result
    assert "Blog Outreach | 1" in result


def test_inject_timestamp(data_dir: Path, dashboard_template: str) -> None:
    result = inject_dashboard_data(dashboard_template, data_dir)
    assert "2026-" in result  # Timestamp injected
    assert "<!-- TIMESTAMP -->" not in result


def test_load_json_missing(tmp_path: Path) -> None:
    assert load_json(tmp_path / "nonexistent.json") is None


def test_load_jsonl_empty(tmp_path: Path) -> None:
    assert load_jsonl(tmp_path / "nonexistent.jsonl") == []


def test_load_jsonl_valid(tmp_path: Path) -> None:
    f = tmp_path / "test.jsonl"
    f.write_text('{"a": 1}\n{"b": 2}\n')
    result = load_jsonl(f)
    assert len(result) == 2
    assert result[0] == {"a": 1}


def test_budget_allocation_nested_format(data_dir: Path, dashboard_template: str) -> None:
    """Test that budget_allocation works with nested dict format too."""
    pc = json.loads((data_dir / "paid_campaigns.json").read_text())
    pc["budget_allocation"] = {
        "apple_search_ads": {"daily_budget_usd": 8.0},
        "google_uac": {"daily_budget_usd": 5.0},
    }
    (data_dir / "paid_campaigns.json").write_text(json.dumps(pc))

    result = inject_dashboard_data(dashboard_template, data_dir)
    assert "$8.00" in result
    assert "$5.00" in result
    assert "$13.00" in result


def test_refreshes_legacy_footer_timestamp(data_dir: Path) -> None:
    template = (
        "# Dashboard\n\n"
        "_Dashboard generated at: `2026-02-21T16:30:28+00:00`. "
        "Data refreshed daily by [`wiki-sync.yml`]"
        "(https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/wiki-sync.yml)._\n"
    )
    result = inject_dashboard_data(template, data_dir)
    assert "2026-02-21T16:30:28+00:00" not in result
    assert "_Dashboard generated at: `" in result
    assert "wiki-sync.yml" in result
