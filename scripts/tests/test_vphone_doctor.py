"""TDD for vphone-cli readiness doctor (virtual iPhone lane)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.vphone_doctor import (
    READY_FOR_VM_CREATE,
    READY_FOR_LAUNCH,
    BLOCKED_SIP_AMFI,
    BLOCKED_CLI_MISSING,
    BLOCKED_NOT_APPLE_SILICON,
    FALLBACK_SIMULATOR,
    classify_readiness,
    build_report,
    main,
)


def test_classify_readiness_requires_apple_silicon() -> None:
    assert (
        classify_readiness(
            apple_silicon=False,
            cli_present=True,
            cli_runs=True,
            sip_relaxed=True,
            amfi_relaxed=True,
            vm_names=["myphone"],
        )
        == BLOCKED_NOT_APPLE_SILICON
    )


def test_classify_readiness_missing_cli() -> None:
    assert (
        classify_readiness(
            apple_silicon=True,
            cli_present=False,
            cli_runs=False,
            sip_relaxed=False,
            amfi_relaxed=False,
            vm_names=[],
        )
        == BLOCKED_CLI_MISSING
    )


def test_classify_readiness_sip_blocks_even_if_cli_installed() -> None:
    assert (
        classify_readiness(
            apple_silicon=True,
            cli_present=True,
            cli_runs=False,
            sip_relaxed=False,
            amfi_relaxed=False,
            vm_names=[],
        )
        == BLOCKED_SIP_AMFI
    )


def test_classify_readiness_cli_runs_but_no_vm_is_create_ready() -> None:
    assert (
        classify_readiness(
            apple_silicon=True,
            cli_present=True,
            cli_runs=True,
            sip_relaxed=True,
            amfi_relaxed=True,
            vm_names=[],
        )
        == READY_FOR_VM_CREATE
    )


def test_classify_readiness_existing_vm_is_launch_ready() -> None:
    assert (
        classify_readiness(
            apple_silicon=True,
            cli_present=True,
            cli_runs=True,
            sip_relaxed=True,
            amfi_relaxed=True,
            vm_names=["rtt-qa"],
        )
        == READY_FOR_LAUNCH
    )


def test_build_report_prefers_simulator_fallback_when_blocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("scripts.vphone_doctor.detect_apple_silicon", lambda: True)
    monkeypatch.setattr("scripts.vphone_doctor.detect_cli_path", lambda: "/opt/homebrew/bin/vphone-cli")
    monkeypatch.setattr("scripts.vphone_doctor.probe_cli_runs", lambda _path: False)
    monkeypatch.setattr(
        "scripts.vphone_doctor.detect_sip_amfi",
        lambda: {"sip_enabled": True, "sip_relaxed": False, "amfi_relaxed": False, "boot_args": None},
    )
    monkeypatch.setattr("scripts.vphone_doctor.list_vm_names", lambda _cli, _root: [])
    monkeypatch.setattr("scripts.vphone_doctor.vphone_root", lambda: tmp_path / ".vphone")

    report = build_report()

    assert report["status"] == BLOCKED_SIP_AMFI
    assert report["fallback"] == FALLBACK_SIMULATOR
    assert report["claim_device_e2e_on_vphone"] is False
    assert "SIP" in report["blockers"][0] or "AMFI" in report["blockers"][0]
    assert report["preferred_over_physical_phone"] is True


def test_main_json_exit_nonzero_when_blocked(capsys, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("scripts.vphone_doctor.detect_apple_silicon", lambda: True)
    monkeypatch.setattr("scripts.vphone_doctor.detect_cli_path", lambda: None)
    monkeypatch.setattr(
        "scripts.vphone_doctor.detect_sip_amfi",
        lambda: {"sip_enabled": True, "sip_relaxed": False, "amfi_relaxed": False, "boot_args": None},
    )
    monkeypatch.setattr("scripts.vphone_doctor.list_vm_names", lambda _cli, _root: [])
    monkeypatch.setattr("scripts.vphone_doctor.vphone_root", lambda: tmp_path / ".vphone")

    code = main(["--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert code == 2
    assert payload["status"] == BLOCKED_CLI_MISSING
    assert payload["fallback"] == FALLBACK_SIMULATOR
