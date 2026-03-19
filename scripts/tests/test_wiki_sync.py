"""Tests for wiki_sync.py — dashboard data injection."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wiki_sync import inject_dashboard_data, inject_paid_acquisition_data, load_json, load_jsonl


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


@pytest.fixture
def paid_template() -> str:
    return textwrap.dedent("""\
        # Paid Acquisition

        <!-- LIVE_PAID_START -->
        old
        <!-- LIVE_PAID_END -->

        <!-- LIVE_PAID_SOURCES_START -->
        old
        <!-- LIVE_PAID_SOURCES_END -->

        <!-- LIVE_PAID_CHARTS_START -->
        old
        <!-- LIVE_PAID_CHARTS_END -->

        <!-- LIVE_PAID_BUDGET_START -->
        old
        <!-- LIVE_PAID_BUDGET_END -->

        <!-- LIVE_CAMPAIGN_STATUS_START -->
        old
        <!-- LIVE_CAMPAIGN_STATUS_END -->
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


def test_inject_paid_uses_apple_live_metrics(data_dir: Path, paid_template: str) -> None:
    (data_dir / "north_star.json").write_text(json.dumps({
        "north_star": {
            "wqtu_7d": 0,
            "targets": {"checkpoint_2026_03_31": 8, "quarter_2026_06_30": 25},
        },
        "paid": {
            "paid_distinct_users_30d": 0,
            "paid_events_by_source_30d": [],
            "active_campaign_count": 1,
            "guardrail_violated": True,
        },
    }))
    (data_dir / "store_downloads.json").write_text(json.dumps({
        "combined": {"downloads_30d": 9},
    }))
    (data_dir / "content_feedback.json").write_text(json.dumps({
        "onboarding_funnel": {"open_to_completed_rate": 0.242},
    }))
    (data_dir / "apple_ads_live_metrics.json").write_text(json.dumps({
        "status": "ok",
        "campaign_count": 1,
        "active_campaign_count": 1,
        "finding": "API reports 1 campaign(s), 1 active; 30d taps 0, spend $0.00, installs 0.",
        "metrics_30d": {
            "impressions": 0,
            "taps": 0,
            "spend_usd": 0.0,
            "installs": 0,
        },
        "snapshots": [
            {"timestamp": "2026-02-24T17:00:00+00:00", "taps": 0, "spend_usd": 0.0},
            {"timestamp": "2026-02-24T17:15:00+00:00", "taps": 1, "spend_usd": 1.23},
        ],
    }))

    result = inject_paid_acquisition_data(paid_template, data_dir)
    assert "Apple Ads Campaigns (API) | 1" in result
    assert "Apple Ads Clicks/Taps (30d) | 0" in result
    assert "Apple Ads Spend (30d) | $0.00" in result
    assert "API reports 1 campaign(s), 1 active" in result
    assert "Apple Ads Taps (30d snapshot trend)" in result
    assert "Platform | Config Status | Live Status | Daily Budget" in result


def test_inject_dashboard_marks_stale_download_proxy_metrics(data_dir: Path) -> None:
    template = textwrap.dedent("""\
        # Dashboard

        <!-- DOWNLOADS_START -->
        old
        <!-- DOWNLOADS_END -->
    """)
    (data_dir / "store_downloads.json").write_text(json.dumps({
        "status": "degraded",
        "generated_at": "2026-03-16T00:00:00+00:00",
        "ios": {"downloads_30d": 4},
        "android": {"downloads_30d": 7, "active_installs": 9},
        "combined": {"downloads_30d": 11},
        "active_users": {"dau": 2, "wau": 5, "mau": 12},
        "metric_definitions": {
            "downloads_30d": {"display_name": "Distinct install users (30d)"}
        },
        "data_quality": {
            "is_stale": True,
            "last_good_generated_at": "2026-03-15T10:00:00+00:00",
            "reason": "http_504",
        },
    }))

    result = inject_dashboard_data(template, data_dir)
    assert "Distinct install users (30d)" in result
    assert "showing last good metrics from `2026-03-15T10:00:00+00:00`" in result
    assert "http_504" in result


def test_inject_dashboard_marks_stale_north_star_and_funnel(data_dir: Path) -> None:
    template = textwrap.dedent("""\
        # Dashboard

        <!-- NORTH_STAR_START -->
        old
        <!-- NORTH_STAR_END -->

        <!-- FUNNEL_START -->
        old
        <!-- FUNNEL_END -->
    """)
    (data_dir / "north_star.json").write_text(json.dumps({
        "status": "degraded",
        "north_star": {
            "wqtu_7d": 9,
            "timer_completed_7d": 27,
            "completed_users_7d": 9,
            "sessions_per_completed_user_7d": 3.0,
            "targets": {"checkpoint_2026_03_31": 8, "quarter_2026_06_30": 25},
        },
        "paid": {"paid_distinct_users_30d": 2, "active_campaign_count": 1, "guardrail_violated": False},
        "data_quality": {
            "is_stale": True,
            "last_good_generated_at": "2026-03-15T10:00:00+00:00",
            "reason": "http_504",
        },
    }))
    (data_dir / "content_feedback.json").write_text(json.dumps({
        "status": "degraded",
        "onboarding_funnel": {
            "first_open": 100,
            "first_timer_configured": 75,
            "first_timer_completed": 30,
            "open_to_configured_rate": 0.75,
            "open_to_completed_rate": 0.30,
        },
        "data_quality": {
            "is_stale": True,
            "last_good_generated_at": "2026-03-15T10:00:00+00:00",
            "reason": "query timeout",
        },
    }))

    result = inject_dashboard_data(template, data_dir)
    assert result.count("_Data quality: stale") == 2
    assert "query timeout" in result


def test_inject_paid_acquisition_marks_stale_sources(data_dir: Path, paid_template: str) -> None:
    (data_dir / "north_star.json").write_text(json.dumps({
        "status": "degraded",
        "north_star": {"wqtu_7d": 1, "targets": {"checkpoint_2026_03_31": 8, "quarter_2026_06_30": 25}},
        "paid": {"paid_distinct_users_30d": 0, "paid_events_by_source_30d": [], "active_campaign_count": 1, "guardrail_violated": False},
        "data_quality": {"is_stale": True, "last_good_generated_at": "2026-03-15T10:00:00+00:00", "reason": "http_504"},
    }))
    (data_dir / "store_downloads.json").write_text(json.dumps({
        "status": "degraded",
        "combined": {"downloads_30d": 9},
        "metric_definitions": {"downloads_30d": {"display_name": "Distinct install users (30d)"}},
        "data_quality": {"is_stale": True, "last_good_generated_at": "2026-03-15T10:00:00+00:00", "reason": "http_504"},
    }))
    (data_dir / "content_feedback.json").write_text(json.dumps({
        "status": "degraded",
        "onboarding_funnel": {"open_to_completed_rate": 0.242},
        "data_quality": {"is_stale": True, "last_good_generated_at": "2026-03-15T10:00:00+00:00", "reason": "query timeout"},
    }))

    result = inject_paid_acquisition_data(paid_template, data_dir)
    assert "Distinct install users (30d)" in result
    assert "showing last good metrics from `2026-03-15T10:00:00+00:00`" in result
