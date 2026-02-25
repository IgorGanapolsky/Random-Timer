from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts import check_store_access as csa


def test_read_service_account_email_from_raw_json():
    email = csa._read_service_account_email(json.dumps({"client_email": "svc@example.com"}))
    assert email == "svc@example.com"


def test_build_asc_jwt_reports_missing_env(monkeypatch):
    monkeypatch.delenv("APPSTORE_KEY_ID", raising=False)
    monkeypatch.delenv("APPSTORE_ISSUER_ID", raising=False)
    monkeypatch.delenv("APPSTORE_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("APPSTORE_PRIVATE_KEY_PATH", raising=False)

    token, err = csa._build_asc_jwt()
    assert token is None
    assert "Missing App Store credentials" in err


def test_check_ios_access_handles_non_json_response(monkeypatch):
    monkeypatch.setattr(csa, "_build_asc_jwt", lambda: ("tok", ""))

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("not json")

    fake_requests = SimpleNamespace(get=lambda *_a, **_k: _Resp())
    monkeypatch.setitem(__import__("sys").modules, "requests", fake_requests)

    ok, summary = csa.check_ios_access("com.example.app")
    assert ok is False
    assert "non-JSON" in summary


def test_check_ios_access_not_found_app(monkeypatch):
    monkeypatch.setattr(csa, "_build_asc_jwt", lambda: ("tok", ""))

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": []}

    fake_requests = SimpleNamespace(get=lambda *_a, **_k: _Resp())
    monkeypatch.setitem(__import__("sys").modules, "requests", fake_requests)

    ok, summary = csa.check_ios_access("com.example.app")
    assert ok is False
    assert "no app found" in summary.lower()
