"""Tests for check_crashlytics.py."""

import importlib
import json
import math
import os
import sys
import types
from unittest.mock import MagicMock, patch


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
    rate = {"rows": [{"f": [{"v": "10"}, {"v": "8"}, {"v": "80.0"}]}]}

    with patch.object(cc, "get_access_token", return_value="token"), \
         patch.object(cc, "check_bigquery_export", return_value=["com_iganapolsky_randomtimer"]), \
         patch.object(cc, "query_crash_summary", return_value=summary), \
         patch.object(cc, "query_crash_free_rate", return_value=rate):
        payload = cc.collect_crashlytics_snapshot(hours=168)

    assert payload["status"] == "ok"
    assert payload["project_id"] == "random-timer-dist-new"
    assert payload["table_id"] == "com_iganapolsky_randomtimer"
    assert payload["fatal_events"] == 3
    assert payload["affected_users"] == 2
    assert payload["total_users"] == 10
    assert payload["crash_free_users"] == 8
    assert math.isclose(payload["crash_free_pct"], 80.0)
    assert payload["top_fatal_issues"][0]["issue_title"] == "Crash title"


def test_collect_crashlytics_snapshot_handles_missing_export():
    with patch.object(cc, "get_access_token", return_value="token"), \
         patch.object(cc, "check_bigquery_export", return_value=None):
        payload = cc.collect_crashlytics_snapshot(hours=24)

    assert payload["status"] == "skipped"
    assert payload["reason"] == "Crashlytics BigQuery export not set up"
