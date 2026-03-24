from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

from scripts import verify_release as vr


class _Resp:
    def __init__(self, status_code: int = 200, payload=None, text: str = ""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("bad")

    def json(self):
        return self._payload


def test_google_play_verifier_extracts_email_from_raw_json():
    gp = vr.GooglePlayVerifier()
    email = gp._extract_service_account_email(json.dumps({"client_email": "svc@example.com"}))
    assert email == "svc@example.com"


def test_poll_until_done_times_out(monkeypatch):
    monkeypatch.setattr(vr.time, "sleep", lambda *_a, **_k: None)

    result = vr.poll_until_done(
        lambda: {"passed": False, "status": "PROCESSING", "details": "still processing"},
        poll_interval=1,
        timeout=0,
    )
    assert result["passed"] is False
    assert "timed out" in result["details"]


def test_appstore_request_non_json_raises(monkeypatch):
    asc = vr.AppStoreVerifier()
    monkeypatch.setattr(asc, "_get_token", lambda: "tok")

    class _BadResp(_Resp):
        def json(self):
            raise ValueError("oops")

    fake_requests = SimpleNamespace(get=lambda *_a, **_k: _BadResp(status_code=200, text="plain"))
    monkeypatch.setitem(__import__("sys").modules, "requests", fake_requests)

    try:
        asc._request("/apps")
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "non-JSON" in str(exc)


def test_print_results_returns_true_only_when_all_pass():
    assert vr.print_results([
        {"platform": "Android", "track": "alpha", "version": "1", "passed": True, "status": "ok", "details": ""}
    ]) is True
    assert vr.print_results([
        {"platform": "Android", "track": "alpha", "version": "1", "passed": False, "status": "bad", "details": "x"}
    ]) is False


def test_resolve_google_play_key_prefers_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_PLAY_JSON_KEY", '{"type":"service_account"}')
    key = vr.GooglePlayVerifier._resolve_google_play_key()
    assert key == '{"type":"service_account"}'


def test_resolve_google_play_key_fallback_to_path(monkeypatch):
    monkeypatch.delenv("GOOGLE_PLAY_JSON_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_PLAY_JSON_KEY_PATH", "/some/path/key.json")
    key = vr.GooglePlayVerifier._resolve_google_play_key()
    assert key == "/some/path/key.json"


def test_extract_service_account_email_from_file(tmp_path):
    key_file = tmp_path / "key.json"
    key_file.write_text(json.dumps({"client_email": "svc@proj.iam.gserviceaccount.com"}))
    gp = vr.GooglePlayVerifier()
    email = gp._extract_service_account_email(str(key_file))
    assert email == "svc@proj.iam.gserviceaccount.com"


def test_extract_service_account_email_returns_none_for_invalid_json():
    gp = vr.GooglePlayVerifier()
    assert gp._extract_service_account_email("not valid json") is None
    assert gp._extract_service_account_email("{}") is None


def test_google_play_verify_found_on_track(monkeypatch):
    gp = vr.GooglePlayVerifier()
    mock_edits = MagicMock()
    mock_edits.insert.return_value.execute.return_value = {"id": "edit-123"}
    mock_edits.tracks.return_value.get.return_value.execute.return_value = {
        "releases": [{"versionCodes": ["42"], "status": "completed"}],
    }
    gp.service = MagicMock(edits=lambda: mock_edits)
    result = gp.verify("alpha", 42)
    assert result["passed"] is True
    assert "42" in result["details"]


def test_google_play_verify_not_found(monkeypatch):
    gp = vr.GooglePlayVerifier()
    mock_edits = MagicMock()
    mock_edits.insert.return_value.execute.return_value = {"id": "edit-123"}
    mock_edits.tracks.return_value.get.return_value.execute.return_value = {
        "releases": [{"versionCodes": ["100"], "status": "completed"}],
    }
    gp.service = MagicMock(edits=lambda: mock_edits)
    result = gp.verify("alpha", 42)
    assert result["passed"] is False
    assert result["status"] == "NOT_FOUND"


def test_google_play_verify_api_error(monkeypatch):
    gp = vr.GooglePlayVerifier()
    mock_edits = MagicMock()
    mock_edits.insert.return_value.execute.side_effect = RuntimeError("403 Forbidden")
    gp.service = MagicMock(edits=lambda: mock_edits)
    result = gp.verify("alpha", 42)
    assert result["passed"] is False
    assert result["status"] == "ERROR"


def test_appstore_verifier_verify_build_found(monkeypatch):
    asc = vr.AppStoreVerifier()
    monkeypatch.setattr(asc, "_get_app_id", lambda: "app-123")
    monkeypatch.setattr(asc, "_request", lambda path, params=None: {
        "data": [
            {
                "id": "b-1",
                "attributes": {"version": "162", "processingState": "VALID", "uploadedDate": "2024-01-01"},
                "relationships": {
                    "preReleaseVersion": {"data": {"id": "prv-1"}},
                },
            },
        ],
        "included": [{"id": "prv-1", "type": "preReleaseVersions", "attributes": {"version": "1.2.3"}}],
    })
    result = asc.verify("1.2.3")
    assert result["passed"] is True
    assert result["status"] == "VALID"


def test_appstore_verifier_verify_build_not_found(monkeypatch):
    asc = vr.AppStoreVerifier()
    monkeypatch.setattr(asc, "_get_app_id", lambda: "app-123")
    monkeypatch.setattr(asc, "_request", lambda path, params=None: {
        "data": [],
        "included": [],
    })
    result = asc.verify("1.2.3")
    assert result["passed"] is False
    assert result["status"] == "NOT_FOUND"


def test_appstore_verifier_app_store_version_not_submitted(monkeypatch):
    asc = vr.AppStoreVerifier()
    monkeypatch.setattr(asc, "_get_app_id", lambda: "app-123")
    monkeypatch.setattr(asc, "_request", lambda path, params=None: {"data": []})
    result = asc.verify_app_store_version("1.2.3")
    assert result["passed"] is True
    assert result["status"] == "NOT_SUBMITTED"


def test_appstore_verifier_app_store_version_submitted(monkeypatch):
    asc = vr.AppStoreVerifier()
    monkeypatch.setattr(asc, "_get_app_id", lambda: "app-123")
    monkeypatch.setattr(
        asc,
        "_request",
        lambda path, params=None: {
            "data": [
                {"id": "v1", "attributes": {"versionString": "1.2.3", "appStoreState": "WAITING_FOR_REVIEW"}},
            ],
        },
    )
    result = asc.verify_app_store_version("1.2.3")
    assert result["passed"] is True
    assert result["status"] == "WAITING_FOR_REVIEW"


def test_poll_until_done_passes_immediately(monkeypatch):
    monkeypatch.setattr(vr.time, "sleep", lambda *_a, **_k: None)
    result = vr.poll_until_done(
        lambda: {"passed": True, "status": "OK", "details": "done"},
        poll_interval=1,
        timeout=10,
    )
    assert result["passed"] is True


def test_poll_until_done_stops_on_terminal_status(monkeypatch):
    monkeypatch.setattr(vr.time, "sleep", lambda *_a, **_k: None)
    result = vr.poll_until_done(
        lambda: {"passed": False, "status": "ERROR", "details": "fatal"},
        poll_interval=1,
        timeout=10,
        terminal_statuses={"ERROR"},
    )
    assert result["passed"] is False
    assert result["status"] == "ERROR"


def test_parse_args_platform_and_version_code(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["verify_release.py", "--platform", "android", "--version-code", "5"],
    )
    a = vr.parse_args()
    assert a.platform == "android"
    assert a.version_code == 5


def test_parse_args_ios_scope(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["verify_release.py", "--platform", "ios", "--version", "1.2.3", "--ios-scope", "testflight"],
    )
    a = vr.parse_args()
    assert a.ios_scope == "testflight"


def test_main_skips_app_store_check_when_ios_scope_is_testflight(monkeypatch):
    build_calls = []
    app_store_calls = []

    class _FakeASC:
        def verify(self, version):
            build_calls.append(version)
            return {"passed": True, "status": "VALID", "details": "ok"}

        def verify_app_store_version(self, version):
            app_store_calls.append(version)
            return {"passed": False, "status": "REJECTED", "details": "bad"}

    monkeypatch.setattr(vr, "AppStoreVerifier", lambda: _FakeASC())
    monkeypatch.setattr(vr, "print_results", lambda results: True)
    monkeypatch.setattr(
        "sys.argv",
        ["verify_release.py", "--platform", "ios", "--version", "1.2.3", "--ios-scope", "testflight"],
    )

    with pytest.raises(SystemExit) as exc:
        vr.main()

    assert exc.value.code == 0
    assert build_calls == ["1.2.3"]
    assert app_store_calls == []
