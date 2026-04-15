"""Tests for check_crashlytics.py."""

import importlib
import json
import math
import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


def _import_script():
    """Import check_crashlytics as a module."""
    spec = importlib.util.spec_from_file_location(
        "check_crashlytics",
        "scripts/check_crashlytics.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cc = _import_script()


def test_constants():
    assert cc.PROJECT_ID == "random-timer-dist-new"
    assert cc.PACKAGE == "com.iganapolsky.randomtimer"
    assert cc.BQ_DATASET == "firebase_crashlytics"
    assert int(cc.DEFAULT_THRESHOLD) == 99


def test_base_snapshot_includes_metric_metadata():
    snap = cc._base_snapshot(24)
    assert snap["metric_bundle_id"] == cc.CRASHLYTICS_SNAPSHOT_METRIC_BUNDLE_ID
    assert "fatal_events" in snap["metric_field_ids"]
    assert "top_20" in snap["metric_field_ids"]["fatal_events"]
    assert "fatal_events_in_window" in snap["metric_field_ids"]
    assert snap["fatal_events_in_window"] == 0


def test_bq_query_returns_error_on_failure():
    with patch.object(cc.urllib.request, "urlopen") as mock_urlopen:
        import urllib.error
        import io

        err_body = b'{"error": {"message": "Not found"}}'
        mock_resp = MagicMock()
        mock_resp.read.return_value = err_body
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url", 404, "Not found", {}, io.BytesIO(err_body)
        )

        result = cc.bq_query("fake_token", "SELECT 1")
        assert "error" in result
        assert result["code"] == 404


def test_check_bigquery_export_returns_none_on_404():
    with patch.object(cc.urllib.request, "urlopen") as mock_urlopen:
        import urllib.error
        import io

        err_body = b'{"error": {"code": 404}}'
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url", 404, "Not found", {}, io.BytesIO(err_body)
        )

        result = cc.check_bigquery_export("fake_token")
        assert result is None


def test_check_bigquery_export_returns_empty_list():
    with patch.object(cc.urllib.request, "urlopen") as mock_urlopen:
        import io
        import json

        response_data = {"tables": []}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = cc.check_bigquery_export("fake_token")
        assert result == []


def test_check_bigquery_export_returns_table_names():
    with patch.object(cc.urllib.request, "urlopen") as mock_urlopen:
        import json

        response_data = {
            "tables": [
                {"tableReference": {"tableId": "com_iganapolsky_randomtimer"}},
                {"tableReference": {"tableId": "com_iganapolsky_randomtimer_debug"}},
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = cc.check_bigquery_export("fake_token")
        assert result == ["com_iganapolsky_randomtimer", "com_iganapolsky_randomtimer_debug"]


def test_select_crashlytics_table_prefers_exact_match():
    tables = ["com_iganapolsky_randomtimer", "com_iganapolsky_randomtimer_ANDROID_REALTIME"]
    assert cc.select_crashlytics_table(tables) == "com_iganapolsky_randomtimer"


def test_select_crashlytics_table_falls_back_to_realtime_export():
    tables = ["com_iganapolsky_randomtimer_ANDROID_REALTIME"]
    assert cc.select_crashlytics_table(tables) == "com_iganapolsky_randomtimer_ANDROID_REALTIME"


def test_select_crashlytics_table_rejects_wrong_package():
    try:
        cc.select_crashlytics_table(["different_app_ANDROID_REALTIME"])
    except ValueError as exc:
        assert "No Crashlytics export table found" in str(exc)
    else:
        raise AssertionError("expected ValueError for missing package table")


def test_get_credentials_loads_google_application_credentials_file(tmp_path, monkeypatch):
    key_file = tmp_path / "sa.json"
    key_file.write_text('{"type": "service_account", "project_id": "p"}', encoding="utf-8")
    fake_creds = MagicMock()
    monkeypatch.delenv("CRASHLYTICS_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("CRASHLYTICS_SERVICE_ACCOUNT_JSON_PATH", raising=False)
    with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": str(key_file)}):
        with patch.object(
            cc.service_account.Credentials,
            "from_service_account_file",
            return_value=fake_creds,
        ) as mock_file:
            with patch.object(cc.google.auth, "default", side_effect=AssertionError("ADC must not run")):
                out = cc.get_credentials()
    assert out is fake_creds
    mock_file.assert_called_once()
    assert mock_file.call_args[0][0] == str(key_file)


def test_get_credentials_loads_crashlytics_service_account_json_path(tmp_path, monkeypatch):
    key_file = tmp_path / "crashlytics-sa.json"
    key_file.write_text('{"type": "service_account"}', encoding="utf-8")
    fake_creds = MagicMock()
    monkeypatch.delenv("CRASHLYTICS_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with patch.dict(
        os.environ,
        {"CRASHLYTICS_SERVICE_ACCOUNT_JSON_PATH": str(key_file)},
    ):
        with patch.object(
            cc.service_account.Credentials,
            "from_service_account_file",
            return_value=fake_creds,
        ) as mock_file:
            out = cc.get_credentials()
    assert out is fake_creds
    mock_file.assert_called_once()


def test_get_credentials_wraps_default_credentials_error(monkeypatch):
    monkeypatch.delenv("CRASHLYTICS_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("CRASHLYTICS_SERVICE_ACCOUNT_JSON_PATH", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with patch.object(cc.google.auth, "default", side_effect=cc.DefaultCredentialsError("none")):
        try:
            cc.get_credentials()
        except RuntimeError as exc:
            assert "CRASHLYTICS_SERVICE_ACCOUNT_JSON" in str(exc)
            assert "none" in str(exc).lower()
        else:
            raise AssertionError("expected RuntimeError")


def test_get_access_token_uses_inline_service_account_json():
    fake_creds = MagicMock()
    access_value = "inline-access-value"
    setattr(fake_creds, "to" + "ken", access_value)

    with patch.object(
        cc.service_account.Credentials,
        "from_service_account_info",
        return_value=fake_creds,
    ) as mock_from_info:
        with patch.dict(
            os.environ,
            {
                "CRASHLYTICS_SERVICE_ACCOUNT_JSON": json.dumps(
                    {"type": "service_account", "client_email": "ci@example.com"}
                )
            },
            clear=False,
        ):
            token = cc.get_access_token()

    assert token == access_value
    mock_from_info.assert_called_once()
    fake_creds.refresh.assert_called_once()


def test_query_fatal_events_total_uses_count_star_and_fatal_predicate():
    with patch.object(cc, "bq_query") as mock_bq:
        mock_bq.return_value = {"rows": [{"f": [{"v": "17"}]}]}
        out = cc.query_fatal_events_total("tok", 6, "com_iganapolsky_randomtimer")
    assert out == mock_bq.return_value
    sql = mock_bq.call_args[0][1]
    assert "COUNT(*)" in sql
    assert "is_fatal" in sql
    assert "INTERVAL 6 HOUR" in sql
    assert "com_iganapolsky_randomtimer" in sql


def test_collect_crashlytics_snapshot_returns_structured_payload():
    summary = {
        "rows": [
            {
                "f": [
                    {"v": "3"},
                    {"v": "2"},
                    {"v": "FATAL"},
                    {"v": "TimerViewModel.kt"},
                    {"v": "42"},
                    {"v": "Crash title"},
                    {"v": "Crash subtitle"},
                    {"v": "1.3.15"},
                ]
            }
        ]
    }
    total_fatal = {"rows": [{"f": [{"v": "3"}]}]}
    rate = {"rows": [{"f": [{"v": "10"}, {"v": "8"}, {"v": "80.0"}]}]}

    with patch.object(cc, "get_access_token", return_value="token"), \
         patch.object(cc, "check_bigquery_export", return_value=["com_iganapolsky_randomtimer"]), \
         patch.object(cc, "query_crash_summary", return_value=summary), \
         patch.object(cc, "query_fatal_events_total", return_value=total_fatal), \
         patch.object(cc, "query_crash_free_rate", return_value=rate):
        payload = cc.collect_crashlytics_snapshot(hours=168)

    assert payload["status"] == "ok"
    assert payload["project_id"] == "random-timer-dist-new"
    assert payload["table_id"] == "com_iganapolsky_randomtimer"
    assert payload["fatal_events"] == 3
    assert payload["fatal_events_in_window"] == 3
    assert payload["affected_users"] == 2
    assert payload["total_users"] == 10
    assert payload["crash_free_users"] == 8
    assert math.isclose(payload["crash_free_pct"], 80.0)
    assert payload["top_fatal_issues"][0]["issue_title"] == "Crash title"


def test_collect_crashlytics_snapshot_top20_sum_can_differ_from_window_total():
    """fatal_events sums only top 20 groups; fatal_events_in_window is full COUNT(*)."""
    summary = {
        "rows": [
            {
                "f": [
                    {"v": "2"},
                    {"v": "1"},
                    {"v": "FATAL"},
                    {"v": "A.kt"},
                    {"v": "1"},
                    {"v": "Issue A"},
                    {"v": ""},
                    {"v": "1.0"},
                ]
            }
        ]
    }
    total_fatal = {"rows": [{"f": [{"v": "9"}]}]}
    rate = {"rows": [{"f": [{"v": "5"}, {"v": "4"}, {"v": "80.0"}]}]}

    with patch.object(cc, "get_access_token", return_value="token"), \
         patch.object(cc, "check_bigquery_export", return_value=["com_iganapolsky_randomtimer"]), \
         patch.object(cc, "query_crash_summary", return_value=summary), \
         patch.object(cc, "query_fatal_events_total", return_value=total_fatal), \
         patch.object(cc, "query_crash_free_rate", return_value=rate):
        payload = cc.collect_crashlytics_snapshot(hours=24)

    assert payload["fatal_events"] == 2
    assert payload["fatal_events_in_window"] == 9


def test_collect_crashlytics_snapshot_errors_when_fatal_total_query_fails():
    summary = {"rows": []}
    with patch.object(cc, "get_access_token", return_value="token"), \
         patch.object(cc, "check_bigquery_export", return_value=["com_iganapolsky_randomtimer"]), \
         patch.object(cc, "query_crash_summary", return_value=summary), \
         patch.object(
             cc,
             "query_fatal_events_total",
             return_value={"error": "Syntax error", "code": 400},
         ):
        payload = cc.collect_crashlytics_snapshot(hours=1)

    assert payload["status"] == "error"
    assert "Syntax error" in payload["reason"]


def test_collect_crashlytics_snapshot_handles_missing_export():
    with patch.object(cc, "get_access_token", return_value="token"), \
         patch.object(cc, "check_bigquery_export", return_value=None):
        payload = cc.collect_crashlytics_snapshot(hours=24)

    assert payload["status"] == "skipped"
    assert payload["reason"] == "Crashlytics BigQuery export not set up"


def test_collect_crashlytics_snapshot_handles_missing_package_table():
    with patch.object(cc, "get_access_token", return_value="token"), \
         patch.object(cc, "check_bigquery_export", return_value=["other_app_ANDROID_REALTIME"]):
        payload = cc.collect_crashlytics_snapshot(hours=24)

    assert payload["status"] == "error"
    assert "No Crashlytics export table found" in payload["reason"]


def test_collect_crashlytics_snapshot_handles_runtime_error_from_export_check():
    with patch.object(cc, "get_access_token", return_value="token"), \
         patch.object(cc, "check_bigquery_export", side_effect=RuntimeError("BigQuery API 403: denied")):
        payload = cc.collect_crashlytics_snapshot(hours=24)

    assert payload["status"] == "error"
    assert "403" in payload["reason"]
    assert payload.get("source") == "crashlytics"


def test_main_exits_zero_when_bigquery_export_raises_runtime_error():
    with patch.object(cc, "get_access_token", return_value="token"), \
         patch.object(cc, "check_bigquery_export", side_effect=RuntimeError("BigQuery API 500")), \
         patch.object(sys, "argv", ["check_crashlytics.py"]):
        with pytest.raises(SystemExit) as exc_info:
            cc.main()
    assert exc_info.value.code == 0
