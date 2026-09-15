#!/usr/bin/env python3
"""GPT-6 Astra harness lite — steal patterns, not the paid API default.

Source:
  https://www.infoq.com/news/2026/09/openai-gpt6-astra/

InfoQ thesis: Astra pushes computer use, coding, long-running Codex notes across
context windows, lower hallucination, and critical cyber capability (production
restricts offense). Highest ROI for Random Timer under the $20/mo hard cap is
**harness discipline**, not defaulting to gpt-6-astra API:

  - Computer-use first when UI exists without a reliable API
  - Searchable session notes (not compaction alone)
  - Confirm consequential actions
  - Tool search instead of dumping full catalogs
  - Evidence before retry; stop after 4 identical failures
  - Cybersecurity: defensive only — block offensive exploit work
  - Monitorability: evidence trails, not opaque “reasoning”
  - Budget-gate any Astra API use; prefer local/subscription paths
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lite_gate_common import (
    Decision,
    norm,
    require_docs_needles,
    require_dual_skills,
    run_presence_cli,
)

SOURCE = "https://www.infoq.com/news/2026/09/openai-gpt6-astra/"

HEALTH_SIGNALS = (
    "computer_use_first",
    "searchable_session_notes",
    "confirm_consequential",
    "tool_search",
    "evidence_before_retry",
    "cyber_defensive_only",
    "monitorability_evidence_trail",
    "budget_gated_astra_api",
    "stay_in_scope",
)

MAX_IDENTICAL_RETRIES = 4

CONSEQUENTIAL_ACTIONS = frozenset(
    {
        "store_publish",
        "force_push",
        "gmail_send",
        "production_deploy",
        "make_purchase",
        "alter_billing",
    }
)

OFFENSIVE_ACTIONS = frozenset(
    {
        "develop_exploit",
        "offensive_cyber",
        "pwn",
        "weaponize_vulnerability",
        "unauthorized_access",
        "write_malware",
    }
)


def select_harness_surface(
    *,
    has_reliable_api: bool,
    has_ui: bool,
    needs_coding_cli: bool,
) -> str:
    if needs_coding_cli and not has_ui:
        return "coding_cli"
    if has_ui and not has_reliable_api:
        return "computer_use"
    if has_reliable_api:
        return "cli_or_api"
    if needs_coding_cli:
        return "coding_cli"
    return "computer_use" if has_ui else "cli_or_api"


def append_session_note(notes_dir: Path, window_id: str, body: str) -> Path:
    """Persist a searchable note for a context window (Astra Codex-style)."""
    notes_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", window_id).strip("_") or "note"
    path = notes_dir / f"{safe}.md"
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    chunk = body.strip() + "\n"
    path.write_text(existing + ("" if not existing else "\n") + chunk, encoding="utf-8")
    return path


def search_session_notes(notes_dir: Path, query: str) -> list[dict[str, str]]:
    """Search prior windows' notes — do not rely on compaction alone."""
    q = query.strip().lower()
    if not q or not notes_dir.is_dir():
        return []
    hits: list[dict[str, str]] = []
    for path in sorted(notes_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if q in text.lower():
            hits.append({"path": str(path), "snippet": text[:240]})
    return hits


def should_retry(
    *,
    identical_failure_count: int,
    new_evidence: bool,
    same_action: bool,
) -> Decision:
    if same_action and identical_failure_count >= MAX_IDENTICAL_RETRIES and not new_evidence:
        return Decision(
            action="block_retry_loop",
            ok=False,
            reason=f"stop after {MAX_IDENTICAL_RETRIES} identical failures without new evidence",
        )
    if same_action and identical_failure_count > 0 and not new_evidence:
        return Decision(
            action="block_retry_without_evidence",
            ok=False,
            reason="evidence before retry: change hypothesis or gather new proof",
        )
    return Decision(
        action="allow_retry_with_evidence",
        ok=True,
        reason="retry allowed with new evidence or fresh action",
    )


def evaluate_harness_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))

    if action in {
        "default_to_astra_api",
        "subscribe_astra_default",
        "always_astra",
    }:
        return Decision(
            action="block_paid_astra_default",
            ok=False,
            reason="do not default to gpt-6-astra API under hard monthly cap — steal harness patterns locally",
        )

    if action in OFFENSIVE_ACTIONS or claim.get("offensive") is True:
        return Decision(
            action="block_offensive_cyber",
            ok=False,
            reason="Astra critical cyber capability: production posture is defensive-only — block offense",
        )

    if action in {"rely_on_compaction_only", "lossy_compaction_only"}:
        return Decision(
            action="block_compaction_only_memory",
            ok=False,
            reason="use searchable session notes across windows — not compaction alone",
        )

    if action in {"dump_full_tool_catalog", "load_all_mcp_tools"}:
        return Decision(
            action="block_full_tool_dump",
            ok=False,
            reason="tool search on demand — do not stuff entire catalogs into context",
        )

    if action == "invent_api" and claim.get("has_ui") is True and claim.get(
        "has_reliable_api"
    ) is not True:
        return Decision(
            action="block_invent_api_use_computer_use",
            ok=False,
            reason="computer-use first when UI exists without a reliable API",
        )

    if action in CONSEQUENTIAL_ACTIONS or claim.get("consequential") is True:
        if claim.get("confirmed") is not True:
            return Decision(
                action="block_unconfirmed_consequential",
                ok=False,
                reason="confirm consequential actions (publish, force-push, send, deploy)",
            )
        return Decision(
            action="allow_confirmed_consequential",
            ok=True,
            reason="consequential action confirmed",
        )

    if action in {"claim_done", "claim_ready", "claim_complete"}:
        if claim.get("evidence_present") is not True:
            return Decision(
                action="block_claim_without_evidence",
                ok=False,
                reason="monitorability: claims need evidence trails (Astra hallucination discipline)",
            )
        return Decision(
            action="allow_evidenced_claim",
            ok=True,
            reason="claim backed by evidence",
        )

    if action in {"retry", "retry_same_action"}:
        return should_retry(
            identical_failure_count=int(claim.get("identical_failure_count") or 0),
            new_evidence=bool(claim.get("new_evidence")),
            same_action=claim.get("same_action", True) is not False,
        )

    if action in {"computer_use", "browser_use", "osworld_style"}:
        if claim.get("scope_ok") is False:
            return Decision(
                action="block_out_of_scope",
                ok=False,
                reason="stay in authorized CEO scope",
            )
        if claim.get("has_ui") is True and claim.get("has_reliable_api") is not True:
            return Decision(
                action="allow_computer_use",
                ok=True,
                reason="computer-use surface selected",
            )
        return Decision(
            action="allow_computer_use",
            ok=True,
            reason="computer-use allowed",
        )

    if action in {"use_astra_api", "call_gpt6_astra"}:
        try:
            budget = float(claim.get("budget_remaining_usd"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            budget = -1.0
        if budget <= 0 or claim.get("named_hard_job") is not True:
            return Decision(
                action="block_unbudgeted_astra",
                ok=False,
                reason="Astra API only for a named hard job with remaining budget",
            )
        if claim.get("api_key_verified") is not True:
            return Decision(
                action="block_unverified_astra_key",
                ok=False,
                reason="verify API key in-session before claiming Astra API live",
            )
        return Decision(
            action="allow_budgeted_astra",
            ok=True,
            reason="budgeted Astra API use for named hard job",
        )

    if action in {"write_session_note", "search_session_notes"}:
        return Decision(
            action="allow_session_notes",
            ok=True,
            reason="searchable session notes path",
        )

    if action in {"select_surface"}:
        surface = select_harness_surface(
            has_reliable_api=bool(claim.get("has_reliable_api")),
            has_ui=bool(claim.get("has_ui")),
            needs_coding_cli=bool(claim.get("needs_coding_cli")),
        )
        return Decision(
            action=f"allow_surface_{surface}",
            ok=True,
            reason=f"selected harness surface: {surface}",
        )

    return Decision(
        action="block_unknown_astra_harness_action",
        ok=False,
        reason=(
            "declare action: computer_use|store_publish|claim_done|retry|"
            "use_astra_api|write_session_note|select_surface"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "GPT6_ASTRA_HARNESS.md").is_file():
        blockers.append("missing_docs/GPT6_ASTRA_HARNESS.md")
    if not (repo / "scripts" / "gpt6_astra_harness_gate.py").is_file():
        blockers.append("missing_scripts/gpt6_astra_harness_gate.py")
    blockers.extend(require_dual_skills(repo, "gpt6-astra-harness-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "GPT6_ASTRA_HARNESS.md",
            (
                "computer-use",
                "session notes",
                "compaction",
                "confirm",
                "tool search",
                "retry",
                "cybersecurity",
                "monitorability",
                "budget",
                "scope",
            ),
        )
    )

    fixture = (
        repo / "marketing" / "data" / "code_health" / "gpt6_astra_harness_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/gpt6_astra_harness_discipline.json"
        )
    else:
        try:
            charter = json.loads(fixture.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blockers.append(f"fixture_invalid_json:{exc}")
        else:
            for signal in HEALTH_SIGNALS:
                if not charter.get(signal):
                    blockers.append(f"fixture_missing:{signal}")
            budget = charter.get("budget") or {}
            if not isinstance(budget, dict) or budget.get("default_to_astra_api") is not False:
                blockers.append("fixture_missing:budget.default_to_astra_api=false")

    example = repo / "marketing" / "data" / "session_notes" / "astra_harness_example.md"
    if not example.is_file():
        blockers.append(
            "missing_fixture:marketing/data/session_notes/astra_harness_example.md"
        )

    ready = len(blockers) == 0
    return {
        "framework": "gpt6-astra-harness-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "max_identical_retries": MAX_IDENTICAL_RETRIES,
        "anti_pattern": "default_paid_astra_api_without_harness_discipline",
        "budget_note": (
            "steal computer-use + searchable notes + confirmations locally; "
            "Astra API only when budgeted named hard job + verified key"
        ),
        "infoq_benchmarks_proxy": {
            "osworld_2_0_pct": 72.6,
            "terminal_bench_4_0_pct": 57.9,
            "hallucination_pct": 4.2,
            "label": "infoq_reported_proxy_not_repo_measured",
        },
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "gpt6-astra-harness-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_harness_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
