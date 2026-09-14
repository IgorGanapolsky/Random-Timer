#!/usr/bin/env python3
"""Report Callstack agent-device readiness for Random Timer runtime evidence.

High-ROI items stolen from Callstack Incubator Aug 2026 dispatch (callstack.pdf):
- Prefer agent-device runtime evidence over green unit CI alone
- Self-host agent-device proxy (Mac mini / local Mac) — zero cloud spend
- Skip Expo EAS cloud simulators / paid Apex until under $20/mo budget

Upstream: https://oss.callstack.com/agent-device/docs/remote-proxy
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any

MIN_NODE_MAJOR = 22
SOURCE = "callstack_dispatch_2026-09"

BLOCKED_NODE_TOO_OLD = "blocked_node_too_old"
BLOCKED_CLI_MISSING = "blocked_cli_missing"
BLOCKED_NO_IOS_TARGETS = "blocked_no_ios_targets"
READY_LOCAL = "ready_local"
READY_PROXY = "ready_proxy"
DEGRADED_CLI_ONLY = "degraded_cli_only"


def parse_node_major(version_text: str) -> int | None:
    match = re.search(r"v?(\d+)", (version_text or "").strip())
    if not match:
        return None
    return int(match.group(1))


def detect_node_major() -> int | None:
    node = shutil.which("node")
    if not node:
        return None
    try:
        completed = subprocess.run(
            [node, "-v"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_node_major(completed.stdout or completed.stderr or "")


def detect_cli() -> str | None:
    return shutil.which("agent-device")


def _npx_agent_device_cmd() -> list[str]:
    npx = shutil.which("npx")
    if not npx:
        return []
    return [npx, "-y", "agent-device"]


def list_ios_devices() -> list[dict[str, Any]]:
    cli = detect_cli()
    cmd = [cli, "devices", "--platform", "ios", "--json"] if cli else []
    if not cmd:
        cmd = _npx_agent_device_cmd()
        if not cmd:
            return []
        cmd.extend(["devices", "--platform", "ios", "--json"])
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    text = (completed.stdout or "").strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    data = payload.get("data") if isinstance(payload, dict) else None
    devices = data.get("devices") if isinstance(data, dict) else None
    if isinstance(devices, list):
        return [d for d in devices if isinstance(d, dict)]
    return []


def _proxy_url_allowed(url: str) -> bool:
    """Only probe loopback / RFC1918 / Tailscale CGNAT — never arbitrary public hosts."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    # Tailscale CGNAT 100.64.0.0/10
    if host.startswith("100."):
        parts = host.split(".")
        if len(parts) == 4 and parts[0] == "100":
            try:
                second = int(parts[1])
            except ValueError:
                return False
            return 64 <= second <= 127
    # RFC1918
    if host.startswith("10.") or host.startswith("192.168."):
        return True
    if host.startswith("172."):
        try:
            second = int(host.split(".")[1])
        except (IndexError, ValueError):
            return False
        return 16 <= second <= 31
    return False


def probe_proxy() -> dict[str, Any]:
    token = os.environ.get("AGENT_DEVICE_DAEMON_AUTH_TOKEN", "").strip()
    base = (
        os.environ.get("AGENT_DEVICE_DAEMON_BASE_URL", "").strip()
        or os.environ.get("AGENT_DEVICE_PROXY_URL", "").strip()
    )
    configured = bool(token and base)
    health_ok = False
    health_error = None
    if configured and not _proxy_url_allowed(base):
        health_error = "proxy_url_not_private_or_loopback"
        configured = True
    elif configured:
        health_url = base.rstrip("/")
        if not health_url.endswith("/health"):
            # Official contract: /health and /agent-device/health
            if "/agent-device" in health_url:
                health_url = health_url.rstrip("/") + "/health"
            else:
                health_url = health_url.rstrip("/") + "/agent-device/health"
        try:
            req = urllib.request.Request(health_url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:  # noqa: S310 — allowlist gated
                health_ok = 200 <= getattr(resp, "status", 200) < 300
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            health_error = str(exc)
            try:
                alt = base.rstrip("/")
                if alt.endswith("/agent-device"):
                    alt = alt[: -len("/agent-device")] + "/health"
                else:
                    alt = alt.rstrip("/") + "/health"
                if not _proxy_url_allowed(alt):
                    raise OSError("proxy_url_not_private_or_loopback")
                with urllib.request.urlopen(alt, timeout=3) as resp:  # noqa: S310
                    health_ok = 200 <= getattr(resp, "status", 200) < 300
                    health_error = None
            except (urllib.error.URLError, TimeoutError, OSError) as exc2:
                health_error = str(exc2)
    return {
        "proxy_env_configured": configured,
        "proxy_health_ok": health_ok,
        "proxy_url": base or None,
        "proxy_health_error": health_error,
        "note": (
            "Prefer Tailscale/SSH tunnel to Mac mini over paid ngrok. "
            "Do not put tokens in repo files."
        ),
    }


def evaluate_status(payload: dict[str, Any]) -> str:
    node_major = payload.get("node_major")
    if node_major is None or int(node_major) < MIN_NODE_MAJOR:
        return BLOCKED_NODE_TOO_OLD
    if not payload.get("cli_available"):
        return BLOCKED_CLI_MISSING
    if payload.get("proxy_env_configured") and payload.get("proxy_health_ok"):
        return READY_PROXY
    if int(payload.get("ios_device_count") or 0) <= 0:
        if payload.get("proxy_env_configured"):
            return DEGRADED_CLI_ONLY
        return BLOCKED_NO_IOS_TARGETS
    if int(payload.get("ios_booted_count") or 0) > 0 or int(payload.get("ios_device_count") or 0) > 0:
        return READY_LOCAL
    return DEGRADED_CLI_ONLY


def build_report() -> dict[str, Any]:
    node_major = detect_node_major()
    cli = detect_cli()
    cli_available = bool(cli) or bool(_npx_agent_device_cmd())
    devices = list_ios_devices() if cli_available else []
    booted = [d for d in devices if d.get("booted")]
    proxy = probe_proxy()
    core = {
        "node_major": node_major,
        "cli_available": cli_available,
        "cli_path": cli,
        "ios_device_count": len(devices),
        "ios_booted_count": len(booted),
        "proxy_env_configured": proxy["proxy_env_configured"],
        "proxy_health_ok": proxy["proxy_health_ok"],
    }
    status = evaluate_status(core)
    claim_ok = status in {READY_LOCAL, READY_PROXY}
    return {
        "source": SOURCE,
        "status": status,
        "min_node_major": MIN_NODE_MAJOR,
        "claim_runtime_evidence": claim_ok,
        "devices_sample": devices[:5],
        "budget": {
            "prefer_zero_cost": True,
            "skip_expo_eas_cloud_simulators": True,
            "skip_paid_apex_until_budgeted": True,
            "prefer_tailscale_or_ssh_over_ngrok": True,
            "cap_usd_month": 20,
        },
        "high_roi_from_dispatch": [
            "agent-device runtime evidence before merge claims",
            "self-host agent-device proxy on Mac with Simulator",
            "PR review loop: open → snapshot → evidence artifacts",
        ],
        "skipped_low_roi_for_native_app": [
            "React Native 0.87 / React Navigation / Rozenite",
            "Margelo Nitro/MMKV (RN stack)",
            "Expo EAS cloud simulator waitlist",
            "Agent Conf tickets / paid Apex GA",
        ],
        **core,
        **{k: proxy[k] for k in ("proxy_url", "proxy_health_error", "note")},
        "docs": [
            "docs/DEVICE_E2E_TESTS.md",
            "https://oss.callstack.com/agent-device/docs/remote-proxy",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="agent-device readiness doctor")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"status={report['status']} claim_runtime_evidence={report['claim_runtime_evidence']}")
        print(
            f"node={report['node_major']} ios_devices={report['ios_device_count']} "
            f"booted={report['ios_booted_count']} proxy={report['proxy_env_configured']}"
        )
    return 0 if report["claim_runtime_evidence"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
