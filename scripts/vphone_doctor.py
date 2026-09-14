#!/usr/bin/env python3
"""Report vphone-cli readiness for a virtual-iPhone device lane.

Upstream: https://github.com/Lakr233/vphone-cli

Agents MUST prefer this lane (or iOS Simulator) over the CEO physical phone.
Do not claim device E2E on vphone unless status is ready_for_launch and Maestro exits 0.
Do not disable SIP/AMFI without explicit CEO risk acceptance.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

BLOCKED_NOT_APPLE_SILICON = "blocked_not_apple_silicon"
BLOCKED_CLI_MISSING = "blocked_cli_missing"
BLOCKED_SIP_AMFI = "blocked_sip_amfi"
READY_FOR_VM_CREATE = "ready_for_vm_create"
READY_FOR_LAUNCH = "ready_for_launch"
FALLBACK_SIMULATOR = "ios_simulator_maestro"

PREFERRED_VARIANTS = ("less", "regular")
SOURCE_URL = "https://github.com/Lakr233/vphone-cli"


def vphone_root() -> Path:
    override = os.environ.get("VPHONE_ROOT", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".vphone"


def detect_apple_silicon() -> bool:
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def detect_cli_path() -> str | None:
    return shutil.which("vphone-cli")


def probe_cli_runs(cli_path: str, timeout_seconds: float = 5.0) -> bool:
    """Return True if the CLI process starts and exits without being killed by AMFI."""
    try:
        completed = subprocess.run(
            [cli_path, "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    # AMFI kill typically yields empty output + non-zero / abnormal termination.
    if completed.returncode != 0 and not (completed.stdout or completed.stderr):
        return False
    return completed.returncode == 0 or bool(completed.stdout or completed.stderr)


def detect_sip_amfi() -> dict[str, Any]:
    sip_enabled = True
    sip_text = ""
    try:
        completed = subprocess.run(
            ["csrutil", "status"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        sip_text = (completed.stdout or completed.stderr or "").strip()
        lowered = sip_text.lower()
        if "disabled" in lowered:
            sip_enabled = False
        elif "enabled" in lowered and "without debug" in lowered:
            # Option B: csrutil enable --without debug counts as SIP-relaxed for amfidont path.
            sip_enabled = True
            return {
                "sip_enabled": True,
                "sip_relaxed": True,
                "amfi_relaxed": False,
                "boot_args": _read_boot_args(),
                "csrutil_status": sip_text,
                "note": "SIP enabled without debug — run vphone-amfidont after Recovery allow-research-guests",
            }
    except (OSError, subprocess.TimeoutExpired):
        sip_text = "unknown"

    boot_args = _read_boot_args()
    amfi_relaxed = bool(boot_args and "amfi_get_out_of_my_way=1" in boot_args)
    sip_relaxed = not sip_enabled
    return {
        "sip_enabled": sip_enabled,
        "sip_relaxed": sip_relaxed,
        "amfi_relaxed": amfi_relaxed,
        "boot_args": boot_args,
        "csrutil_status": sip_text or "unknown",
    }


def _read_boot_args() -> str | None:
    try:
        completed = subprocess.run(
            ["nvram", "boot-args"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (completed.stdout or "").strip()
    if not text or "data was not found" in (completed.stderr or ""):
        return None
    # nvram prints: boot-args	value
    if "\t" in text:
        return text.split("\t", 1)[1].strip()
    return text


def list_vm_names(cli_path: str | None, root: Path) -> list[str]:
    library = Path(os.environ.get("VPHONE_LIBRARY_ROOT", "")).expanduser() if os.environ.get("VPHONE_LIBRARY_ROOT") else root / "VMs"
    if library.is_dir():
        names = sorted(p.name for p in library.iterdir() if p.is_dir() and not p.name.startswith("."))
        if names:
            return names
    if not cli_path:
        return []
    try:
        completed = subprocess.run(
            [cli_path, "vm", "list", "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0 or not completed.stdout.strip():
        return []
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(payload, list):
        names: list[str] = []
        for item in payload:
            if isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict) and item.get("name"):
                names.append(str(item["name"]))
        return names
    if isinstance(payload, dict):
        vms = payload.get("vms") or payload.get("items") or []
        if isinstance(vms, list):
            return [str(v.get("name") if isinstance(v, dict) else v) for v in vms if v]
    return []


def classify_readiness(
    *,
    apple_silicon: bool,
    cli_present: bool,
    cli_runs: bool,
    sip_relaxed: bool,
    amfi_relaxed: bool,
    vm_names: list[str],
) -> str:
    if not apple_silicon:
        return BLOCKED_NOT_APPLE_SILICON
    if not cli_present:
        return BLOCKED_CLI_MISSING
    host_ok = sip_relaxed and (amfi_relaxed or cli_runs)
    if not host_ok:
        return BLOCKED_SIP_AMFI
    if not cli_runs:
        return BLOCKED_SIP_AMFI
    if vm_names:
        return READY_FOR_LAUNCH
    return READY_FOR_VM_CREATE


def build_report() -> dict[str, Any]:
    apple_silicon = detect_apple_silicon()
    cli_path = detect_cli_path()
    cli_present = bool(cli_path)
    cli_runs = probe_cli_runs(cli_path) if cli_path else False
    sip = detect_sip_amfi()
    root = vphone_root()
    vm_names = list_vm_names(cli_path, root)
    status = classify_readiness(
        apple_silicon=apple_silicon,
        cli_present=cli_present,
        cli_runs=cli_runs,
        sip_relaxed=bool(sip.get("sip_relaxed")),
        amfi_relaxed=bool(sip.get("amfi_relaxed")),
        vm_names=vm_names,
    )

    blockers: list[str] = []
    if status == BLOCKED_NOT_APPLE_SILICON:
        blockers.append("Host is not Apple Silicon Darwin — Virtualization PV=3 guests are unsupported.")
    elif status == BLOCKED_CLI_MISSING:
        blockers.append("vphone-cli not on PATH. Install: brew install --cask zqxwce/tap/vphone-cli (trust tap first).")
    elif status == BLOCKED_SIP_AMFI:
        blockers.append(
            "SIP/AMFI not relaxed for private PV=3 entitlements. "
            "CEO must pick Recovery Option A (disable SIP + amfi boot-arg) or Option B "
            "(csrutil enable --without debug + allow-research-guests + vphone-amfidont). "
            "Do not relax SIP without explicit CEO acceptance."
        )
        if cli_present and not cli_runs:
            blockers.append("vphone-cli is installed but killed at launch (typical AMFI denial).")

    claim_ok = status == READY_FOR_LAUNCH
    return {
        "source": SOURCE_URL,
        "status": status,
        "fallback": FALLBACK_SIMULATOR,
        "preferred_over_physical_phone": True,
        "claim_device_e2e_on_vphone": claim_ok,
        "apple_silicon": apple_silicon,
        "cli": {
            "present": cli_present,
            "path": cli_path or "",
            "runs": cli_runs,
            "amfidont_present": bool(shutil.which("vphone-amfidont")),
        },
        "sip_amfi": sip,
        "vphone_root": str(root),
        "vms": vm_names,
        "preferred_variants": list(PREFERRED_VARIANTS),
        "blockers": blockers,
        "next_commands": _next_commands(status, vm_names),
        "product_use": (
            "Isolated Random Timer paywall/timer Maestro smoke without contending for the CEO handset. "
            "Prefer variant less|regular for app QA; jb/exp only when sideload/research is required."
        ),
    }


def _next_commands(status: str, vm_names: list[str]) -> list[str]:
    if status == BLOCKED_CLI_MISSING:
        return [
            "brew trust zqxwce/tap",
            "brew install --cask zqxwce/tap/vphone-cli",
            "python3 scripts/vphone_doctor.py --json",
        ]
    if status == BLOCKED_SIP_AMFI:
        return [
            "# Recovery Option B (minimal): csrutil enable --without debug && csrutil allow-research-guests enable",
            "vphone-amfidont",
            "python3 scripts/vphone_doctor.py --json",
            "./scripts/device-tests/run-ios-simulator.sh --maestro --smoke-only",
        ]
    if status == READY_FOR_VM_CREATE:
        return [
            "vphone-cli vm create rtt-qa -V regular",
            "vphone-cli vm launch rtt-qa",
            "./scripts/device-tests/run-ios-vphone.sh --vm rtt-qa --smoke-only",
        ]
    if status == READY_FOR_LAUNCH:
        name = vm_names[0] if vm_names else "rtt-qa"
        return [
            f"vphone-cli vm launch {name}",
            f"./scripts/device-tests/run-ios-vphone.sh --vm {name} --smoke-only",
        ]
    return ["./scripts/device-tests/run-ios-simulator.sh --maestro --smoke-only"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="vphone-cli readiness doctor for Random Timer")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status={report['status']}")
        print(f"fallback={report['fallback']}")
        print(f"claim_device_e2e_on_vphone={report['claim_device_e2e_on_vphone']}")
        for blocker in report["blockers"]:
            print(f"blocker: {blocker}")
        for cmd in report["next_commands"]:
            print(f"next: {cmd}")
    if report["status"] in {READY_FOR_LAUNCH, READY_FOR_VM_CREATE}:
        return 0
    if report["status"] == BLOCKED_NOT_APPLE_SILICON:
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
