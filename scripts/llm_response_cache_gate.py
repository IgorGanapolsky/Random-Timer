#!/usr/bin/env python3
"""LLM response-cache lite — skip repeat inference when fingerprints match.

Source:
  https://thenewstack.io/llm-response-caching-costs/

TNS thesis: fingerprint request + context + model settings + source version +
access scope; exact-match first; measure hit rate before projecting savings;
never cache PII/creative/realtime; shadow then validate before write-back.

High-ROI steals for Random Timer (hard monthly budget — no Redis/vector SaaS):
  - Exact-match SHA-256 keys for batch/CI/boilerplate LLM calls
  - Gate no-cache categories before any store write
  - Require measured hit_rate_pct before savings claims
  - Shadow mode before promoting cache hits into production paths
"""

from __future__ import annotations

import hashlib
import json
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

SOURCE = "https://thenewstack.io/llm-response-caching-costs/"

HEALTH_SIGNALS = (
    "fingerprint_exact_match_first",
    "measure_hit_rate_before_savings",
    "skip_pii_creative_realtime",
    "shadow_then_promote",
)

NO_CACHE_CATEGORIES = frozenset(
    {"pii", "account", "personal", "creative", "realtime", "live", "stock", "inventory"}
)


def fingerprint(query: str, ctx: Mapping[str, object]) -> str:
    """Exact-match key: normalized query + ordered ctx fields that change answers."""
    payload = {
        "query": " ".join(str(query or "").split()).strip().lower(),
        "model": norm(ctx.get("model")),
        "settings": ctx.get("settings") or {},
        "source_version": norm(ctx.get("source_version")),
        "access_scope": norm(ctx.get("access_scope")),
        "documents": ctx.get("documents") or [],
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def evaluate_cache_claim(claim: Mapping[str, object]) -> Decision:
    category = norm(claim.get("category") or claim.get("data_category"))
    mode = norm(claim.get("mode") or claim.get("cache_mode"))
    action = norm(claim.get("action"))

    if category in NO_CACHE_CATEGORIES or action in {"cache_pii", "cache_creative", "cache_realtime"}:
        return Decision(
            action="block_no_cache_category",
            ok=False,
            reason="skip PII/account, creative, and realtime answers — do not cache",
        )

    if action in {"claim_savings", "project_savings"} and claim.get("hit_rate_pct") is None:
        return Decision(
            action="block_unmeasured_savings",
            ok=False,
            reason="measure hit_rate_pct before projecting response-cache savings",
        )

    if action in {"claim_savings", "project_savings"}:
        hit = float(claim.get("hit_rate_pct") or 0)
        if hit <= 0:
            return Decision(
                action="block_unmeasured_savings",
                ok=False,
                reason="hit_rate_pct must be > 0 after measurement",
            )

    if mode == "prompt_cache" and bool(claim.get("count_as_full_skip")):
        return Decision(
            action="block_prompt_cache_as_response_skip",
            ok=False,
            reason="prompt caching reduces prompt rates; it is not a full response skip",
        )

    if mode == "shadow":
        return Decision(
            action="allow_shadow_observe",
            ok=True,
            reason="shadow mode logs would-be hits without changing behavior",
        )

    if action in {"exact_match_lookup", "promote_validated_hit", "claim_savings"}:
        if not bool(claim.get("validated", True)):
            return Decision(
                action="block_unvalidated_writeback",
                ok=False,
                reason="validate responses before write-back to avoid cache poison",
            )
        return Decision(
            action="allow_response_cache",
            ok=True,
            reason="exact-match / measured savings path with validation",
        )

    return Decision(
        action="block_unknown_cache_action",
        ok=False,
        reason="declare action: exact_match_lookup|promote_validated_hit|claim_savings|shadow",
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "LLM_RESPONSE_CACHE.md").is_file():
        blockers.append("missing_docs/LLM_RESPONSE_CACHE.md")
    if not (repo / "scripts" / "llm_response_cache_gate.py").is_file():
        blockers.append("missing_scripts/llm_response_cache_gate.py")
    blockers.extend(require_dual_skills(repo, "llm-response-cache-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "LLM_RESPONSE_CACHE.md",
            (
                "fingerprint",
                "hit rate",
                "prompt caching",
                "shadow",
                "pii",
                "exact",
            ),
        )
    )

    fixture = (
        repo / "marketing" / "data" / "code_health" / "llm_response_cache_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/llm_response_cache_discipline.json"
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
            if not isinstance(budget, dict) or budget.get("subscribe_managed_cache") is not False:
                blockers.append("fixture_missing:budget.subscribe_managed_cache=false")

    ready = len(blockers) == 0
    return {
        "framework": "llm-response-cache-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "anti_pattern": "re_answer_unchanged_work",
        "budget_note": "exact-match fingerprint locally; no managed Redis/vector under hard cap",
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "llm-response-cache-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_cache_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
