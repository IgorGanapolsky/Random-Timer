"""Tests for executive_metrics_snapshot PostHog wiring."""

from __future__ import annotations

import pytest


def test_posthog_section_skipped_without_credentials() -> None:
    from scripts import executive_metrics_snapshot as ems

    out = ems._posthog_section("299775", "", 30)
    assert out["status"] == "skipped"


def test_posthog_metric_field_ids_include_paywall_platform_splits() -> None:
    from scripts import executive_metrics_snapshot as ems

    mf = ems.POSTHOG_EXECUTIVE_METRIC_FIELD_IDS
    assert mf.get("events_paywall_purchase_success_ios")
    assert mf.get("events_paywall_purchase_success_android")
    assert mf.get("distinct_persons_paywall_purchase_success_ios")
    assert mf.get("distinct_persons_paywall_purchase_success_android")


def test_posthog_section_includes_metric_field_ids_when_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import executive_metrics_snapshot as ems

    import store_downloads_snapshot as sds

    def fake_posthog_query(
        query: str,
        api_key: str,
        project_id: str,
        errors: list,
        **kwargs: object,
    ):
        if "interval 7 day" in query and "HAVING count() >= 3" in query:
            return {"results": [[0]]}
        if "review_prompt_requested" in query:
            return {"results": [[0, 0]]}
        if "$screen" in query:
            return {"results": []}
        if "paywall_viewed" in query and "count(DISTINCT person_id)" in query:
            return {"results": [[5]]}
        if "sum(toFloatOrZero(coalesce(toString(properties.revenue)" in query:
            return {"results": [[19.99]]}
        if "$pageview" in query and "utm_medium" in query:
            return {"results": [[2]]}
        return {"results": [[0]]}

    monkeypatch.setattr(sds, "posthog_query", fake_posthog_query)

    out = ems._posthog_section("299775", "test-key", 30)
    assert out["status"] == "ok"
    assert out.get("metric_bundle_id") == ems.POSTHOG_EXECUTIVE_METRIC_BUNDLE_ID
    mf = out.get("metric_field_ids") or {}
    assert mf.get("wqtu_7d_distinct_persons") == (
        "posthog_hogql_wqtu_timer_completed_ge3_trailing_7d_fixed"
    )
    assert mf.get("distinct_persons_application_installed") == (
        "posthog_hogql_distinct_persons_event_application_installed"
    )
    assert out.get("events_paywall_purchase_success_ios") == 0
    assert out.get("distinct_persons_paywall_purchase_success_android") == 0
    assert out.get("paywall_revenue_sum_event_properties") == pytest.approx(19.99)
    assert out.get("paywall_viewed_distinct_persons") == 5
    assert out.get("paywall_purchaser_conversion_from_viewed_pct") == pytest.approx(0.0)
    assert out.get("distinct_persons_pageview_utm_cpc_ppc_paid") == 2
    mf2 = out.get("metric_field_ids") or {}
    assert mf2.get("paywall_revenue_sum_event_properties")


def test_pragmatic_live_excludes_non_store_distribution_channels() -> None:
    from scripts import executive_metrics_snapshot as ems

    assert "distribution_channel" in ems.PRAGMATIC_LIVE
    assert "testflight" in ems.PRAGMATIC_LIVE
    assert "non_play_install" in ems.PRAGMATIC_LIVE


def test_redact_audience_sql_strips_person_uuid_list() -> None:
    from scripts import executive_metrics_snapshot as ems

    raw = (
        "( x ) AND person_id NOT IN ('11111111-1111-1111-1111-111111111111', "
        "'22222222-2222-2222-2222-222222222222')"
    )
    red = ems._redact_audience_sql_for_json(raw)
    assert "11111111" not in red
    assert "redacted" in red.lower()


def test_posthog_person_id_exclusion_sql_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import executive_metrics_snapshot as ems

    monkeypatch.delenv("POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS", raising=False)
    assert ems._posthog_person_id_exclusion_sql() == ""
    monkeypatch.setenv(
        "POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS",
        "11111111-1111-1111-1111-111111111111,not-a-uuid",
    )
    sql = ems._posthog_person_id_exclusion_sql()
    assert "person_id NOT IN" in sql
    assert "11111111-1111-1111-1111-111111111111" in sql
    assert "not-a-uuid" not in sql


def test_posthog_section_includes_wqtu_7d_from_queries(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import executive_metrics_snapshot as ems

    import store_downloads_snapshot as sds

    def fake_posthog_query(
        query: str,
        api_key: str,
        project_id: str,
        errors: list,
        **kwargs: object,
    ):
        if "interval 7 day" in query and "HAVING count() >= 3" in query:
            return {"results": [[99]]}
        if "review_prompt_requested" in query:
            return {"results": [[1, 1]]}
        if "$screen" in query:
            return {"results": [["Timer Setup", 2, 3]]}
        if "paywall_viewed" in query and "count(DISTINCT person_id)" in query:
            return {"results": [[10]]}
        if "sum(toFloatOrZero(coalesce(toString(properties.revenue)" in query:
            return {"results": [[0.0]]}
        if "$pageview" in query and "utm_medium" in query:
            return {"results": [[0]]}
        return {"results": [[0]]}

    monkeypatch.setattr(sds, "posthog_query", fake_posthog_query)

    out = ems._posthog_section("299775", "test-key", 30)
    assert out["status"] == "ok"
    assert out["wqtu_7d_distinct_persons"] == 99
    assert out["window_days"] == 30
