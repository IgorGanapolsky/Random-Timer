"""Tests for check_crashlytics.py."""

import importlib
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
    assert cc.PROJECT_ID == "random-timer-486213"
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
