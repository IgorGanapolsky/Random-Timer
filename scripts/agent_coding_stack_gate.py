#!/usr/bin/env python3
"""Presence gate for the layered agent coding stack (SSOT).

Verifies docs + scripts for OpenGSD, Spec Kit, Superpowers, BMAD-lite,
Compound Engineering lite, Value Center lite, Workflow Economics lite,
Agent Integrity lite, Maintainability Gap lite, Diff Delta lite, Looped Flows lite,
DAIR Academy Daily lite, and LLM Response Cache lite. Does NOT require an
active GSD phase to be ship_ready (that is phase-local).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_DOCS = (
    "docs/AGENT_CODING_STACK.md",
    "docs/GSD_OPENGSD.md",
    "docs/SPEC_KIT.md",
    "docs/SUPERPOWERS.md",
    "docs/BMAD.md",
    "docs/COMPOUND_ENGINEERING.md",
    "docs/PSTACK.md",
    "docs/VALUE_CENTER.md",
    "docs/WORKFLOW_ECONOMICS.md",
    "docs/AGENT_INTEGRITY.md",
    "docs/MAINTAINABILITY_GAP.md",
    "docs/DIFF_DELTA.md",
    "docs/LOOPED_FLOWS.md",
    "docs/DAIR_ACADEMY_DAILY.md",
    "docs/LLM_RESPONSE_CACHE.md",
    "AGENTS.md",
    "CLAUDE.md",
)

REQUIRED_SCRIPTS = (
    "scripts/gsd_phase_gate.py",
    "scripts/speckit_gate.py",
    "scripts/superpowers_gate.py",
    "scripts/bmad_readiness_gate.py",
    "scripts/compound_gate.py",
    "scripts/pstack_gate.py",
    "scripts/value_center_gate.py",
    "scripts/workflow_economics_gate.py",
    "scripts/agent_integrity_gate.py",
    "scripts/maintainability_gap_gate.py",
    "scripts/diff_delta_gate.py",
    "scripts/looped_flows_gate.py",
    "scripts/dair_academy_gate.py",
    "scripts/llm_response_cache_gate.py",
)

BANNED_MARKERS = (
    "gsd-build/get-shit-done",
)


def _run_json(repo: Path, script: str, extra: list[str] | None = None) -> dict[str, Any]:
    cmd = [sys.executable, str(repo / script), "--json", *(extra or [])]
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=False)
    if proc.returncode not in (0, 1):
        return {"ok": False, "error": proc.stderr.strip() or proc.stdout.strip() or f"exit_{proc.returncode}"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid_json:{exc}"}


def evaluate(root: Path) -> dict[str, Any]:
    blockers: list[str] = []
    for rel in REQUIRED_DOCS + REQUIRED_SCRIPTS:
        if not (root / rel).is_file():
            blockers.append(f"missing:{rel}")

    # Ban archived predecessor references in the SSOT doc body as install target
    ssot = root / "docs" / "AGENT_CODING_STACK.md"
    if ssot.is_file():
        text = ssot.read_text(encoding="utf-8")
        if "open-gsd/gsd-core" not in text:
            blockers.append("ssot_missing_open-gsd_pointer")
        if "Do **not** use archived" not in text and "Do not use archived" not in text:
            blockers.append("ssot_missing_archived_ban")

    child: dict[str, Any] = {}
    # Superpowers / BMAD / Compound should be ready at rest
    child["superpowers"] = _run_json(root, "scripts/superpowers_gate.py")
    if not child["superpowers"].get("ready"):
        blockers.append("superpowers_not_ready")

    child["bmad"] = _run_json(root, "scripts/bmad_readiness_gate.py", ["--feature", "002"])
    if not child["bmad"].get("ready"):
        blockers.append("bmad_fixture_not_ready")

    child["compound"] = _run_json(root, "scripts/compound_gate.py", ["--slug", "003"])
    if not child["compound"].get("ready"):
        blockers.append("compound_fixture_not_ready")

    child["pstack"] = _run_json(root, "scripts/pstack_gate.py")
    if not child["pstack"].get("ready"):
        blockers.append("pstack_not_ready")

    child["value_center"] = _run_json(root, "scripts/value_center_gate.py")
    if not child["value_center"].get("ready"):
        blockers.append("value_center_not_ready")

    child["workflow_economics"] = _run_json(root, "scripts/workflow_economics_gate.py")
    if not child["workflow_economics"].get("ready"):
        blockers.append("workflow_economics_not_ready")

    child["agent_integrity"] = _run_json(root, "scripts/agent_integrity_gate.py")
    if not child["agent_integrity"].get("ready"):
        blockers.append("agent_integrity_not_ready")

    child["maintainability_gap"] = _run_json(root, "scripts/maintainability_gap_gate.py")
    if not child["maintainability_gap"].get("ready"):
        blockers.append("maintainability_gap_not_ready")

    child["diff_delta"] = _run_json(root, "scripts/diff_delta_gate.py")
    if not child["diff_delta"].get("ready"):
        blockers.append("diff_delta_not_ready")

    child["looped_flows"] = _run_json(root, "scripts/looped_flows_gate.py")
    if not child["looped_flows"].get("ready"):
        blockers.append("looped_flows_not_ready")

    child["dair_academy"] = _run_json(root, "scripts/dair_academy_gate.py")
    if not child["dair_academy"].get("ready"):
        blockers.append("dair_academy_not_ready")

    child["llm_response_cache"] = _run_json(root, "scripts/llm_response_cache_gate.py")
    if not child["llm_response_cache"].get("ready"):
        blockers.append("llm_response_cache_not_ready")

    child["speckit"] = _run_json(root, "scripts/speckit_gate.py")
    if child["speckit"].get("error"):
        blockers.append("speckit_gate_error")
    elif not child["speckit"].get("constitution", {}).get("ok"):
        blockers.append("speckit_constitution_missing")

    child["gsd"] = _run_json(root, "scripts/gsd_phase_gate.py")
    if child["gsd"].get("error"):
        blockers.append("gsd_gate_error")
    elif child["gsd"].get("source") != "open-gsd/gsd-core":
        blockers.append("gsd_not_open-gsd_source")
    # ship_ready may be false between phases — that is OK for stack presence

    # Soft check: OpenCode optional
    opencode = None
    which = subprocess.run(["which", "opencode"], capture_output=True, text=True, check=False)
    if which.returncode == 0:
        opencode = which.stdout.strip()

    ready = len(blockers) == 0
    return {
        "source": "agent-coding-stack-ssot",
        "ready": ready,
        "claim_done_allowed": ready,
        "blockers": blockers,
        "banned": list(BANNED_MARKERS),
        "opencode_cli": opencode,
        "opencode_required": False,
        "children": {
            "superpowers_ready": child["superpowers"].get("ready"),
            "bmad_ready": child["bmad"].get("ready"),
            "compound_ready": child["compound"].get("ready"),
            "pstack_ready": child["pstack"].get("ready"),
            "value_center_ready": child["value_center"].get("ready"),
            "workflow_economics_ready": child["workflow_economics"].get("ready"),
            "agent_integrity_ready": child["agent_integrity"].get("ready"),
            "maintainability_gap_ready": child["maintainability_gap"].get("ready"),
            "diff_delta_ready": child["diff_delta"].get("ready"),
            "looped_flows_ready": child["looped_flows"].get("ready"),
            "dair_academy_ready": child["dair_academy"].get("ready"),
            "llm_response_cache_ready": child["llm_response_cache"].get("ready"),
            "speckit_implement_ready": child["speckit"].get("implement_ready"),
            "gsd_source": child["gsd"].get("source"),
            "gsd_ship_ready": child["gsd"].get("ship_ready"),
            "gsd_note": "ship_ready=false is OK when no active phase",
        },
        "docs": list(REQUIRED_DOCS),
        "next_step": "use_layered_stack" if ready else "repair_missing_layers",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent coding stack presence gate")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate(Path(args.repo_root).resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"ready={report['ready']} blockers={report['blockers']}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
