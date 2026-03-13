from __future__ import annotations

import json
from types import SimpleNamespace

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


def test_appstore_rejected_state_is_allowed_before_submission(monkeypatch):
    asc = vr.AppStoreVerifier()
    monkeypatch.setattr(asc, "_get_app_id", lambda: "app123")
    monkeypatch.setattr(
        asc,
        "_request",
        lambda *_a, **_k: {
            "data": [
                {
                    "attributes": {
                        "versionString": "1.2.6",
                        "appStoreState": "REJECTED",
                    }
                }
            ]
        },
    )

    result = asc.verify_app_store_version("1.2.6")
    assert result["passed"] is True
    assert result["status"] == "REJECTED"


def test_appstore_rejected_state_fails_when_submission_required(monkeypatch):
    asc = vr.AppStoreVerifier()
    monkeypatch.setattr(asc, "_get_app_id", lambda: "app123")
    monkeypatch.setattr(
        asc,
        "_request",
        lambda *_a, **_k: {
            "data": [
                {
                    "attributes": {
                        "versionString": "1.2.6",
                        "appStoreState": "REJECTED",
                    }
                }
            ]
        },
    )

    result = asc.verify_app_store_version("1.2.6", require_submission=True)
    assert result["passed"] is False
    assert result["status"] == "REJECTED"


def test_appstore_missing_version_only_fails_when_submission_required(monkeypatch):
    asc = vr.AppStoreVerifier()
    monkeypatch.setattr(asc, "_get_app_id", lambda: "app123")
    monkeypatch.setattr(asc, "_request", lambda *_a, **_k: {"data": []})

    pre_submit = asc.verify_app_store_version("1.2.6")
    post_submit = asc.verify_app_store_version("1.2.6", require_submission=True)

    assert pre_submit["passed"] is True
    assert pre_submit["status"] == "NOT_SUBMITTED"
    assert post_submit["passed"] is False
    assert post_submit["status"] == "NOT_SUBMITTED"
