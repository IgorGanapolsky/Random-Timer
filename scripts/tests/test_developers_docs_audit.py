"""Tests for unified developer docs hub (Pi DX playbook adaptations)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "developers_docs_audit.py"
HUB = ROOT / "docs" / "DEVELOPERS.md"
CAPS = ROOT / "docs" / "developer_capabilities.json"
SITE_HUB = ROOT / "marketing" / "site" / "developers.md"
SITE_CAPS = ROOT / "marketing" / "site" / "developer_capabilities.json"


def test_hub_and_catalog_exist() -> None:
    assert HUB.is_file()
    assert CAPS.is_file()
    assert SITE_HUB.is_file()
    assert SITE_CAPS.is_file()


def test_catalog_schema_and_journey_sections() -> None:
    payload = json.loads(CAPS.read_text(encoding="utf-8"))
    assert payload["brand"] == "Random Tactical Timer"
    assert "capabilities" in payload and len(payload["capabilities"]) >= 5
    required = {"id", "name", "status", "platforms", "summary", "evidence_paths"}
    for cap in payload["capabilities"]:
        assert required <= set(cap.keys()), cap
        assert cap["status"] in {"ga", "partial", "planned"}
        assert cap["evidence_paths"], cap["id"]
    journey = payload.get("developer_journey") or []
    assert [step["id"] for step in journey] == [
        "get_started",
        "local_build",
        "integrate_capabilities",
        "store_launch",
    ]


def test_hub_contains_journey_anchors() -> None:
    text = HUB.read_text(encoding="utf-8")
    for needle in (
        "## 1. Get started",
        "## 2. Local build",
        "## 3. Integrate capabilities",
        "## 4. Store launch",
        "developer_capabilities.json",
        "Local storage",
        "Native share",
    ):
        assert needle in text, needle


def test_audit_script_passes() -> None:
    assert SCRIPT.is_file()
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert report["ok"] is True
    assert report["broken_links"] == []
