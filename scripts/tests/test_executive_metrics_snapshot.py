"""Tests for executive_metrics_snapshot PostHog wiring."""

from __future__ import annotations

import sys
import types
from pathlib import Path

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
    assert mf.get("distinct_persons_application_installed_ios")
    assert mf.get("distinct_persons_application_installed_android")
    assert mf.get("distinct_persons_application_opened_ios")
    assert mf.get("distinct_persons_application_opened_android")


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
    assert out.get("distinct_persons_application_installed_ios") == 0
    assert out.get("distinct_persons_application_opened_android") == 0


def test_run_payload_includes_canonical_users_when_posthog_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import executive_metrics_snapshot as ems

    monkeypatch.setattr(ems, "_posthog_section", lambda *_a, **_k: {"status": "ok", "window_days": 30, "wqtu_7d_distinct_persons": 12, "distinct_persons_application_installed": 100, "distinct_persons_timer_completed": 40, "distinct_persons_paywall_purchase_success": 0, "events_paywall_purchase_success": 0})
    monkeypatch.setattr(ems, "load_repo_dotenv", lambda *_a, **_k: None)

    fake_store = types.SimpleNamespace(
        _get_android_data=lambda _d: {"status": "skipped"},
        _get_ios_data=lambda _d: {"status": "skipped"},
    )
    fake_crash = types.SimpleNamespace(
        collect_crashlytics_snapshot=lambda **_k: {"status": "skipped"}
    )
    fake_refunds = types.SimpleNamespace(run=lambda **_k: {"status": "skipped"})
    monkeypatch.setitem(sys.modules, "real_store_downloads", fake_store)
    monkeypatch.setitem(sys.modules, "check_crashlytics", fake_crash)
    monkeypatch.setitem(sys.modules, "check_refunds", fake_refunds)

    payload = ems.run(Path("."), days=30, crashlytics_hours=168, load_dotenv=False)
    canonical = payload.get("canonical_users") or {}
    assert canonical.get("wqtu_7d") == 12
    assert canonical.get("paywall_purchase_success_persons_30d") == 0


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
        return {"results": [[0]]}

    monkeypatch.setattr(sds, "posthog_query", fake_posthog_query)

    out = ems._posthog_section("299775", "test-key", 30)
    assert out["status"] == "ok"
    assert out["wqtu_7d_distinct_persons"] == 99
    assert out["window_days"] == 30


def test_run_includes_refunds_and_uninstall_proxy_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from scripts import executive_metrics_snapshot as ems

    monkeypatch.setattr(
        ems,
        "_posthog_section",
        lambda _proj, _key, _days: {
            "status": "ok",
            "distinct_persons_application_installed_ios": 10,
            "distinct_persons_application_installed_android": 20,
            "distinct_persons_application_opened_ios": 8,
            "distinct_persons_application_opened_android": 15,
        },
    )
    monkeypatch.setattr(
        ems,
        "_posthog_credentials",
        lambda: ("k", "p"),
    )

    fake_crashlytics = types.SimpleNamespace(
        collect_crashlytics_snapshot=lambda hours: {"status": "ok", "hours": hours}
    )
    fake_real_store = types.SimpleNamespace(
        _get_android_data=lambda days: {
            "status": "ok",
            "refund_requests_30d": 3,
            "refund_count_metric_id": "android_refund_metric_id",
            "voided_purchase_reason_counts": {"0": 2, "1": 1},
        },
        _get_ios_data=lambda days: {
            "status": "ok",
            "ios_refund_units_30d": 2,
            "refund_count_metric_id": "ios_refund_metric_id",
            "sales_report_vendor_number_present": True,
            "sales_report_days_with_data": 18,
        },
    )
    monkeypatch.setitem(sys.modules, "check_crashlytics", fake_crashlytics)
    monkeypatch.setitem(sys.modules, "real_store_downloads", fake_real_store)

    payload = ems.run(tmp_path, days=30, load_dotenv=False)

    assert payload["refunds"]["android_refund_requests_30d"] == 3
    assert payload["refunds"]["android_reason_counts"] == {"0": 2, "1": 1}
    assert payload["refunds"]["ios_refund_units_30d"] == 2
    assert payload["refunds"]["ios_refund_count_metric_id"] == "ios_refund_metric_id"
    assert payload["refunds"]["ios_sales_report_days_with_data"] == 18
    assert payload["uninstalls"]["ios_uninstall_proxy_30d"] == 2
    assert payload["uninstalls"]["android_uninstall_proxy_30d"] == 5
