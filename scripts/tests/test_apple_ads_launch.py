from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class _Resp:
    def __init__(self, status_code: int = 200, payload=None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _import_module(monkeypatch):
    fake_jwt = types.SimpleNamespace(encode=lambda *_a, **_k: "tok")
    fake_requests = types.SimpleNamespace(post=lambda *_a, **_k: _Resp())
    monkeypatch.setitem(sys.modules, "jwt", fake_jwt)
    monkeypatch.setitem(sys.modules, "requests", fake_requests)
    sys.modules.pop("apple_ads_launch", None)
    return importlib.import_module("apple_ads_launch")


def test_safe_json_rejects_non_dict(monkeypatch):
    mod = _import_module(monkeypatch)
    with pytest.raises(RuntimeError):
        mod._safe_json(_Resp(200, payload=[1, 2, 3]), "ctx")


def test_get_access_token_requires_access_token(monkeypatch):
    mod = _import_module(monkeypatch)
    monkeypatch.setenv("APPLE_ADS_CLIENT_ID", "cid")

    def fake_post(*_a, **_k):
        return _Resp(200, payload={"token_type": "Bearer"})

    monkeypatch.setattr(mod.requests, "post", fake_post)
    with pytest.raises(RuntimeError):
        mod.get_access_token("secret")


def test_add_negative_keywords_counts_created(monkeypatch):
    mod = _import_module(monkeypatch)

    def fake_post(_path, _headers, _payload):
        return {"data": [{"id": 1}, {"id": 2}]}

    monkeypatch.setattr(mod, "api_post", fake_post)
    created = mod.add_negative_keywords({"Authorization": "x"}, 123, ["free", "music"])
    assert created == 2
