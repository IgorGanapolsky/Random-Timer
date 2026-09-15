"""TDD: TNS LLM response-cache lite — fingerprint, hit-rate, no-cache categories."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts.llm_response_cache_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_cache_claim,
    fingerprint,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "LLM_RESPONSE_CACHE.md").write_text(
        "\n".join(
            [
                "# LLM response cache",
                "fingerprint exact match first",
                "measure hit rate before savings",
                "prompt caching is not response skip",
                "shadow then promote",
                "skip pii creative realtime",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "llm_response_cache_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "llm-response-cache-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# llm-response-cache-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "llm_response_cache_discipline.json").write_text(
        json.dumps(
            {
                "fingerprint_exact_match_first": True,
                "measure_hit_rate_before_savings": "x",
                "skip_pii_creative_realtime": "y",
                "shadow_then_promote": "z",
                "budget": {"subscribe_managed_cache": False},
            }
        )
    )


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertEqual(len(HEALTH_SIGNALS), 4)


class FingerprintTests(unittest.TestCase):
    def test_same_inputs_same_key(self) -> None:
        ctx: dict[str, Any] = {
            "model": "flash",
            "settings": {"temp": 0},
            "source_version": "v1",
            "access_scope": "public",
        }
        a = fingerprint("What is WQTU?", ctx)
        b = fingerprint("  what   is   wqtu? ", ctx)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)

    def test_scope_splits_keys(self) -> None:
        base = {"model": "flash", "settings": {}, "source_version": "v1"}
        a = fingerprint("policy?", {**base, "access_scope": "user-a"})
        b = fingerprint("policy?", {**base, "access_scope": "user-b"})
        self.assertNotEqual(a, b)


class ClaimTests(unittest.TestCase):
    def test_pii_blocked(self) -> None:
        d = evaluate_cache_claim({"category": "pii", "action": "exact_match_lookup"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_no_cache_category")

    def test_unmeasured_savings_blocked(self) -> None:
        d = evaluate_cache_claim({"action": "claim_savings"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unmeasured_savings")

    def test_prompt_cache_not_full_skip(self) -> None:
        d = evaluate_cache_claim(
            {"mode": "prompt_cache", "count_as_full_skip": True, "action": "claim_savings", "hit_rate_pct": 50}
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_prompt_cache_as_response_skip")

    def test_shadow_allowed(self) -> None:
        d = evaluate_cache_claim({"mode": "shadow", "action": "exact_match_lookup"})
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_shadow_observe")

    def test_measured_exact_allowed(self) -> None:
        d = evaluate_cache_claim(
            {"action": "claim_savings", "hit_rate_pct": 40, "validated": True}
        )
        self.assertTrue(d.ok)


class PresenceTests(unittest.TestCase):
    def test_missing_docs_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = evaluate(Path(tmp))
            self.assertFalse(report["ready"])
            self.assertIn("missing_docs/LLM_RESPONSE_CACHE.md", report["blockers"])

    def test_wired_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
