#!/usr/bin/env python3
"""Gemini 3.8 Live + Live Extended Thinking lite — dual-mode voice/agent routing.

Source:
  https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-live-gemini-3-8-live-extended-thinking/

Google thesis (2026-09-15): two Live dialogue models — **3.8 Live** for fluid,
cost-efficient conversations with visual grounding; **3.8 Live Extended Thinking**
for high-complexity multi-step agentic work that *reasons and speaks at the same
time*. Tools run in the background while dialogue continues. Highest ROI under
the $20/mo hard cap is **routing + narration discipline**, not default paid Live
API spend:

  - Dual-mode: Live for scale/cost; Extended Thinking for complex agent workflows
  - Early verbal cues + live progress narration during long tool runs
  - Background tool/API calls while conversation continues (no freeze)
  - Visual grounding when a camera/UI frame is available
  - Barge-in / interruption-friendly turns
  - SynthID watermark awareness for AI audio outputs
  - Prefer free/local/subscription Gemini surfaces; budget-gate Live API
"""

from __future__ import annotations

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

SOURCE = (
    "https://blog.google/innovation-and-ai/models-and-research/gemini-models/"
    "gemini-3-8-live-gemini-3-8-live-extended-thinking/"
)

HEALTH_SIGNALS = (
    "dual_mode_live_vs_extended_thinking",
    "early_verbal_ack_cues",
    "live_progress_narration",
    "background_tools_while_speaking",
    "visual_grounding_when_available",
    "barge_in_friendly",
    "synthid_audio_watermark_awareness",
    "budget_gated_live_api",
    "prefer_free_or_subscription_surfaces",
)

COMPLEXITY_MARKERS = frozenset(
    {
        "multi_step",
        "booking",
        "agentic",
        "code_generation",
        "deep_research",
        "reconcile",
        "planning",
        "tool_heavy",
    }
)


def select_live_mode(
    *,
    complexity: str = "simple",
    needs_visual: bool = False,
    cost_sensitive: bool = True,
) -> str:
    """Pick Live vs Extended Thinking without requiring paid API by default."""
    c = norm(complexity) or "simple"
    if c in COMPLEXITY_MARKERS or c == "complex":
        return "extended_thinking"
    if needs_visual and not cost_sensitive:
        return "live"
    if cost_sensitive:
        return "live"
    return "live"


def narration_plan(*, mode: str, task: str) -> dict[str, Any]:
    """Early ack + progress narration while tools run in background."""
    m = norm(mode) or "live"
    early = "Let me check that…"
    if m == "extended_thinking":
        return {
            "mode": "extended_thinking",
            "early_cue": early,
            "progress_narration": True,
            "background_tools": True,
            "speak_while_reasoning": True,
            "task": task.strip(),
        }
    return {
        "mode": "live",
        "early_cue": early,
        "progress_narration": False,
        "background_tools": True,
        "speak_while_reasoning": False,
        "task": task.strip(),
    }


def evaluate_live_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))

    if action in {
        "default_paid_live_api",
        "always_gemini_live_api",
        "subscribe_live_api_default",
    }:
        return Decision(
            action="block_paid_live_api_default",
            ok=False,
            reason=(
                "do not default to paid Gemini Live API under hard monthly cap — "
                "use dual-mode routing + free/subscription surfaces first"
            ),
        )

    if action in {"freeze_until_tools_done", "block_speech_during_tools"}:
        return Decision(
            action="block_frozen_dialogue",
            ok=False,
            reason="background tools while speaking — keep dialogue fluid (3.8 Live)",
        )

    if action in {"silent_long_tool_run", "no_progress_narration"}:
        if claim.get("mode") == "extended_thinking" or claim.get("complex") is True:
            return Decision(
                action="block_silent_complex_run",
                ok=False,
                reason="Extended Thinking: early cue + live progress narration required",
            )

    if action in {"select_mode", "route_live"}:
        mode = select_live_mode(
            complexity=str(claim.get("complexity") or "simple"),
            needs_visual=bool(claim.get("needs_visual")),
            cost_sensitive=claim.get("cost_sensitive", True) is not False,
        )
        return Decision(
            action=f"allow_mode_{mode}",
            ok=True,
            reason=f"selected Gemini Live mode: {mode}",
        )

    if action in {"narrate", "progress_plan"}:
        plan = narration_plan(
            mode=str(claim.get("mode") or "live"),
            task=str(claim.get("task") or ""),
        )
        if plan["mode"] == "extended_thinking" and not plan["progress_narration"]:
            return Decision(
                action="block_missing_narration",
                ok=False,
                reason="extended_thinking requires progress narration",
            )
        return Decision(
            action="allow_narration_plan",
            ok=True,
            reason=f"narration plan ready ({plan['mode']})",
        )

    if action in {"use_live_api", "call_gemini_38_live"}:
        try:
            budget = float(claim.get("budget_remaining_usd"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            budget = -1.0
        if budget <= 0 or claim.get("named_hard_job") is not True:
            return Decision(
                action="block_unbudgeted_live_api",
                ok=False,
                reason="Live API only for a named hard job with remaining budget",
            )
        if claim.get("api_key_verified") is not True:
            return Decision(
                action="block_unverified_live_key",
                ok=False,
                reason="verify Gemini API key in-session before claiming Live API live",
            )
        return Decision(
            action="allow_budgeted_live_api",
            ok=True,
            reason="budgeted Gemini Live API use for named hard job",
        )

    if action in {"emit_ai_audio", "tts_audio"}:
        if claim.get("synthid_aware") is not True:
            return Decision(
                action="block_unmarked_ai_audio_claim",
                ok=False,
                reason="SynthID watermark awareness required for AI audio outputs",
            )
        return Decision(
            action="allow_synthid_aware_audio",
            ok=True,
            reason="SynthID-aware audio path",
        )

    if action in {"visual_ground", "camera_context"}:
        if claim.get("frame_available") is not True:
            return Decision(
                action="block_visual_without_frame",
                ok=False,
                reason="visual grounding needs an available frame/UI snapshot",
            )
        return Decision(
            action="allow_visual_grounding",
            ok=True,
            reason="visual grounding allowed",
        )

    return Decision(
        action="block_unknown_gemini_live_action",
        ok=False,
        reason=(
            "declare action: select_mode|narrate|use_live_api|"
            "emit_ai_audio|visual_ground|default_paid_live_api"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "GEMINI_38_LIVE_EXTENDED_THINKING.md").is_file():
        blockers.append("missing_docs/GEMINI_38_LIVE_EXTENDED_THINKING.md")
    if not (repo / "scripts" / "gemini_38_live_extended_thinking_gate.py").is_file():
        blockers.append("missing_scripts/gemini_38_live_extended_thinking_gate.py")
    blockers.extend(require_dual_skills(repo, "gemini-38-live-extended-thinking-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "GEMINI_38_LIVE_EXTENDED_THINKING.md",
            (
                "3.8 live",
                "extended thinking",
                "background",
                "progress",
                "visual",
                "barge",
                "synthid",
                "budget",
                "dual-mode",
                "voice",
            ),
        )
    )

    fixture = (
        repo
        / "marketing"
        / "data"
        / "code_health"
        / "gemini_38_live_extended_thinking_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/gemini_38_live_extended_thinking_discipline.json"
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
            if (
                not isinstance(budget, dict)
                or budget.get("default_to_paid_live_api") is not False
            ):
                blockers.append(
                    "fixture_missing:budget.default_to_paid_live_api=false"
                )

    ready = len(blockers) == 0
    return {
        "framework": "gemini-38-live-extended-thinking-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "anti_pattern": "paid_live_api_default_or_silent_tool_freeze",
        "budget_note": (
            "prefer free/subscription Gemini Live surfaces; dual-mode routing; "
            "budget-gate Live API under $20/mo hard cap"
        ),
        "pairs_with": [
            "docs/GPT6_ASTRA_HARNESS.md",
            "docs/HYDRAFUSION_ROUTING.md",
            "docs/GEMINI.md",
            "docs/NVIDIA_PAIR_LOCAL_ROUTER.md",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "gemini-38-live-extended-thinking-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_live_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
