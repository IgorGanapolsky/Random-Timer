from __future__ import annotations

import json

import pytest

from scripts import check_refunds


def test_fetch_refund_events_continues_when_empty_page_has_cursor(monkeypatch):
    pages = [
        {"success": True, "result": [], "result_info": {"count": 0, "cursor": "next"}},
        {"success": True, "result": [{"name": "refund:1"}], "result_info": {"count": 1}},
    ]
    seen_cursors: list[str] = []

    def fake_list_keys(token, account_id, namespace_id, prefix="", cursor=""):
        seen_cursors.append(cursor)
        return pages.pop(0)

    def fake_get_value(token, account_id, namespace_id, key):
        return json.dumps({"notification_uuid": "1"})

    monkeypatch.setattr(check_refunds, "list_kv_keys", fake_list_keys)
    monkeypatch.setattr(check_refunds, "get_kv_value", fake_get_value)

    events = check_refunds.fetch_all_refund_events("token", "account", "namespace")

    assert seen_cursors == ["", "next"]
    assert events == [{"notification_uuid": "1"}]


def test_fetch_lifecycle_events_continues_when_empty_page_has_cursor(monkeypatch):
    pages = [
        {"success": True, "result": [], "result_info": {"count": 0, "cursor": "next"}},
        {
            "success": True,
            "result": [{"name": "subscription_lifecycle:1"}],
            "result_info": {"count": 1},
        },
    ]
    seen_cursors: list[str] = []

    def fake_list_keys(token, account_id, namespace_id, prefix="", cursor=""):
        seen_cursors.append(cursor)
        return pages.pop(0)

    def fake_get_value(token, account_id, namespace_id, key):
        return json.dumps({"notification_uuid": "1"})

    monkeypatch.setattr(check_refunds, "list_kv_keys", fake_list_keys)
    monkeypatch.setattr(check_refunds, "get_kv_value", fake_get_value)

    events = check_refunds.fetch_all_lifecycle_events("token", "account", "namespace")

    assert seen_cursors == ["", "next"]
    assert events == [{"notification_uuid": "1"}]


def test_fetch_lifecycle_events_raises_on_kv_list_error(monkeypatch):
    def fake_list_keys(token, account_id, namespace_id, prefix="", cursor=""):
        return {"success": False, "errors": [{"code": 10000, "message": "rate limited"}]}

    monkeypatch.setattr(check_refunds, "list_kv_keys", fake_list_keys)

    with pytest.raises(RuntimeError, match="KV list_keys failed"):
        check_refunds.fetch_all_lifecycle_events("token", "account", "namespace")
