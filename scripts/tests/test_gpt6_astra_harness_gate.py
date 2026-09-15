"""TDD: GPT-6 Astra harness lite — notes, computer-use, confirm, cyber deny."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.gpt6_astra_harness_gate import (
    HEALTH_SIGNALS,
    MAX_IDENTICAL_RETRIES,
    append_session_note,
    evaluate,
    evaluate_harness_claim,
    search_session_notes,
    select_harness_surface,
    should_retry,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "GPT6_ASTRA_HARNESS.md").write_text(
        "\n".join(
            [
                "# GPT-6 Astra harness",
                "computer-use first",
                "searchable session notes",
                "not compaction alone",
                "confirm consequential",
                "tool search",
                "evidence before retry",
                "cybersecurity defensive only",
                "monitorability evidence trail",
                "budget-gated astra api",
                "stay in scope",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "gpt6_astra_harness_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "gpt6-astra-harness-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# gpt6-astra-harness-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "gpt6_astra_harness_discipline.json").write_text(
        json.dumps(
            {
                "computer_use_first": True,
                "searchable_session_notes": True,
                "confirm_consequential": True,
                "tool_search": True,
                "evidence_before_retry": True,
                "cyber_defensive_only": True,
                "monitorability_evidence_trail": True,
                "budget_gated_astra_api": True,
                "stay_in_scope": True,
                "budget": {"default_to_astra_api": False},
            }
        )
    )
    notes = root / "marketing" / "data" / "session_notes"
    notes.mkdir(parents=True)
    (notes / "astra_harness_example.md").write_text(
        "# note\nsource: play console\nrequirement: production track\n",
        encoding="utf-8",
    )


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertGreaterEqual(len(HEALTH_SIGNALS), 8)

    def test_max_retries(self) -> None:
        self.assertEqual(MAX_IDENTICAL_RETRIES, 4)


class SurfaceTests(unittest.TestCase):
    def test_ui_without_api_uses_computer_use(self) -> None:
        self.assertEqual(
            select_harness_surface(
                has_reliable_api=False, has_ui=True, needs_coding_cli=False
            ),
            "computer_use",
        )

    def test_reliable_api_uses_cli(self) -> None:
        self.assertEqual(
            select_harness_surface(
                has_reliable_api=True, has_ui=True, needs_coding_cli=False
            ),
            "cli_or_api",
        )

    def test_coding_prefers_cli(self) -> None:
        self.assertEqual(
            select_harness_surface(
                has_reliable_api=False, has_ui=False, needs_coding_cli=True
            ),
            "coding_cli",
        )


class NotesTests(unittest.TestCase):
    def test_searchable_notes_across_windows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "notes"
            root.mkdir()
            append_session_note(
                root,
                "window-1",
                "Requirement: production track only. Test: assembleDebug passed.",
            )
            append_session_note(
                root,
                "window-2",
                "Tool output: Play Console showed production release.",
            )
            hits = search_session_notes(root, "production track")
            self.assertTrue(hits)
            self.assertTrue(any("window-1" in h["path"] for h in hits))


class RetryTests(unittest.TestCase):
    def test_blocks_fifth_identical_retry(self) -> None:
        d = should_retry(
            identical_failure_count=4,
            new_evidence=False,
            same_action=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_retry_loop")

    def test_allows_retry_with_new_evidence(self) -> None:
        d = should_retry(
            identical_failure_count=3,
            new_evidence=True,
            same_action=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_retry_with_evidence")


class ClaimTests(unittest.TestCase):
    def test_default_astra_api_blocked(self) -> None:
        d = evaluate_harness_claim({"action": "default_to_astra_api"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_astra_default")

    def test_offensive_cyber_blocked(self) -> None:
        d = evaluate_harness_claim({"action": "develop_exploit", "offensive": True})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_offensive_cyber")

    def test_compaction_only_memory_blocked(self) -> None:
        d = evaluate_harness_claim({"action": "rely_on_compaction_only"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_compaction_only_memory")

    def test_dump_all_tools_blocked(self) -> None:
        d = evaluate_harness_claim({"action": "dump_full_tool_catalog"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_full_tool_dump")

    def test_consequential_without_confirm_blocked(self) -> None:
        d = evaluate_harness_claim(
            {
                "action": "store_publish",
                "consequential": True,
                "confirmed": False,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unconfirmed_consequential")

    def test_invent_api_when_ui_blocked(self) -> None:
        d = evaluate_harness_claim(
            {
                "action": "invent_api",
                "has_ui": True,
                "has_reliable_api": False,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_invent_api_use_computer_use")

    def test_claim_without_evidence_blocked(self) -> None:
        d = evaluate_harness_claim(
            {"action": "claim_done", "evidence_present": False}
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_claim_without_evidence")

    def test_computer_use_allowed(self) -> None:
        d = evaluate_harness_claim(
            {
                "action": "computer_use",
                "has_ui": True,
                "has_reliable_api": False,
                "scope_ok": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_computer_use")

    def test_confirmed_consequential_allowed(self) -> None:
        d = evaluate_harness_claim(
            {
                "action": "store_publish",
                "consequential": True,
                "confirmed": True,
                "evidence_present": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_confirmed_consequential")

    def test_budgeted_astra_allowed(self) -> None:
        d = evaluate_harness_claim(
            {
                "action": "use_astra_api",
                "budget_remaining_usd": 5.0,
                "named_hard_job": True,
                "api_key_verified": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_budgeted_astra")


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])
            self.assertEqual(report["framework"], "gpt6-astra-harness-lite")

    def test_evaluate_missing_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            (root / "docs" / "GPT6_ASTRA_HARNESS.md").unlink()
            report = evaluate(root)
            self.assertFalse(report["ready"])


if __name__ == "__main__":
    unittest.main()
