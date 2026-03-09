from __future__ import annotations

import json
import tempfile
from pathlib import Path
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


def test_write_results_json_writes_report(tmp_path):
    out = tmp_path / "verify-release.json"
    rows = [
        {"platform": "Android", "track": "internal", "version": "42", "passed": True, "status": "completed", "details": "ok"}
    ]

    vr.write_results_json(rows, out)

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["all_passed"] is True
    assert payload["results"][0]["platform"] == "Android"
    assert payload["results"][0]["track"] == "internal"


def test_write_json_report_persists_results_and_summary():
    payload = [
        {"platform": "Android", "track": "internal", "version": "11", "passed": True, "status": "completed", "details": ""},
        {"platform": "iOS", "track": "TestFlight", "version": "1.2.2", "passed": True, "status": "VALID", "details": ""},
    ]

    with tempfile.TemporaryDirectory() as td:
        out = vr.write_json_report(Path(td) / "release-proof.json", payload)

        stored = json.loads(out.read_text(encoding="utf-8"))
        assert stored["all_passed"] is True
        assert len(stored["results"]) == 2
