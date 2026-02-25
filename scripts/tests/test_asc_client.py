from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from scripts import asc_client as ac


def test_safe_json_response_handles_non_json():
    class _Resp:
        content = b"x"
        text = "plain"

        def json(self):
            raise ValueError("bad")

    parsed = ac.safe_json_response(_Resp())
    assert "raw" in parsed


def test_auth_from_env_requires_values(monkeypatch):
    monkeypatch.delenv("APPSTORE_KEY_ID", raising=False)
    monkeypatch.delenv("APPSTORE_ISSUER_ID", raising=False)
    monkeypatch.delenv("APPSTORE_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("APPSTORE_PRIVATE_KEY_PATH", raising=False)
    with pytest.raises(ac.AscClientError):
        ac.ASCAuth.from_env()


def test_request_raises_on_http_error(monkeypatch):
    auth = ac.ASCAuth(key_id="kid", issuer_id="iss", private_key="pk")
    client = ac.ASCClient(auth=auth)
    monkeypatch.setattr(client, "token_value", lambda: "tok")

    class _Resp:
        status_code = 500
        content = b"x"
        text = "boom"

        def json(self):
            return {"error": "boom"}

    fake_requests = SimpleNamespace(request=lambda *_a, **_k: _Resp())
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    with pytest.raises(ac.AscClientError):
        client.request("GET", "/apps")


def test_get_all_follows_next_links(monkeypatch):
    auth = ac.ASCAuth(key_id="kid", issuer_id="iss", private_key="pk")
    client = ac.ASCClient(auth=auth)

    payloads = [
        {"data": [{"id": "1"}], "links": {"next": f"{ac.APP_STORE_CONNECT_API}/apps?page=2"}},
        {"data": [{"id": "2"}], "links": {}},
    ]

    def fake_get(_path, params=None):
        return payloads.pop(0)

    monkeypatch.setattr(client, "get", fake_get)
    items = client.get_all("/apps")
    assert [i["id"] for i in items] == ["1", "2"]
