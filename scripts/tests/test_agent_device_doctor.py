"""Tests for Callstack agent-device doctor (zero-cost ROI from Callstack dispatch)."""

from __future__ import annotations

import json

from scripts import agent_device_doctor as add


def test_parse_node_major() -> None:
    assert add.parse_node_major("v26.7.0") == 26
    assert add.parse_node_major("v22.0.0") == 22
    assert add.parse_node_major("bad") is None


def test_evaluate_status_blocked_node() -> None:
    payload = {
        "node_major": 20,
        "cli_available": True,
        "ios_device_count": 1,
        "ios_booted_count": 0,
        "proxy_env_configured": False,
        "proxy_health_ok": False,
    }
    assert add.evaluate_status(payload) == add.BLOCKED_NODE_TOO_OLD


def test_evaluate_status_ready_local() -> None:
    payload = {
        "node_major": 22,
        "cli_available": True,
        "ios_device_count": 2,
        "ios_booted_count": 1,
        "proxy_env_configured": False,
        "proxy_health_ok": False,
    }
    assert add.evaluate_status(payload) == add.READY_LOCAL


def test_evaluate_status_ready_proxy() -> None:
    payload = {
        "node_major": 26,
        "cli_available": True,
        "ios_device_count": 0,
        "ios_booted_count": 0,
        "proxy_env_configured": True,
        "proxy_health_ok": True,
    }
    assert add.evaluate_status(payload) == add.READY_PROXY


def test_proxy_url_allowlist() -> None:
    assert add._proxy_url_allowed("http://127.0.0.1:4310/agent-device")
    assert add._proxy_url_allowed("http://100.94.135.78:4310/agent-device")
    assert add._proxy_url_allowed("http://192.168.1.10:4310/health")
    assert not add._proxy_url_allowed("https://evil.example.com/agent-device")
    assert not add._proxy_url_allowed("https://trycloudflare.com/agent-device")


def test_build_report_json_roundtrip(monkeypatch) -> None:
    monkeypatch.setattr(add, "detect_node_major", lambda: 26)
    monkeypatch.setattr(add, "detect_cli", lambda: "/usr/bin/agent-device")
    monkeypatch.setattr(
        add,
        "list_ios_devices",
        lambda: [{"id": "x", "booted": True, "name": "iPhone"}],
    )
    monkeypatch.setattr(
        add,
        "probe_proxy",
        lambda: {
            "proxy_env_configured": False,
            "proxy_health_ok": False,
            "proxy_url": None,
            "proxy_health_error": None,
            "note": "test",
        },
    )
    report = add.build_report()
    assert report["status"] == add.READY_LOCAL
    assert report["claim_runtime_evidence"] is True
    assert report["source"] == "callstack_dispatch_2026-09"
    raw = json.dumps(report)
    assert add.READY_LOCAL in raw
