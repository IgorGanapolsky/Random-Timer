"""TDD: NVIDIA PAIR workloads-history telemetry (Personal-AI-Router ground truth)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.nvidia_pair_workloads import (
    UPSTREAM_GITHUB,
    default_workloads_history_path,
    evaluate_multinode_from_workloads,
    summarize_workloads,
)


class SummarizeTests(unittest.TestCase):
    def test_single_node_not_multinode(self) -> None:
        rows = [
            {
                "id": "1",
                "model": "m",
                "engine": "ollama",
                "state": "completed",
                "scheduledOn": "node-a",
                "originatedFrom": "node-a",
            },
            {
                "id": "2",
                "model": "m",
                "engine": "ollama",
                "state": "completed",
                "scheduledOn": "node-a",
                "originatedFrom": "node-a",
            },
        ]
        report = summarize_workloads(rows)
        self.assertEqual(report["job_count"], 2)
        self.assertEqual(report["distinct_scheduled_on"], ["node-a"])
        self.assertFalse(report["multinode"])

    def test_two_scheduled_on_is_multinode(self) -> None:
        rows = [
            {"id": "1", "scheduledOn": "a", "originatedFrom": "a", "state": "completed"},
            {"id": "2", "scheduledOn": "b", "originatedFrom": "a", "state": "completed"},
        ]
        report = summarize_workloads(rows)
        self.assertTrue(report["multinode"])
        self.assertEqual(sorted(report["distinct_scheduled_on"]), ["a", "b"])


class ClaimTests(unittest.TestCase):
    def test_claim_blocked_without_multinode_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workloads-history.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "1",
                            "scheduledOn": "only",
                            "originatedFrom": "only",
                            "state": "completed",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            d = evaluate_multinode_from_workloads(path)
            self.assertFalse(d["ok"])
            self.assertEqual(d["reason"], "single_node_only")

    def test_claim_allowed_with_two_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workloads-history.json"
            path.write_text(
                json.dumps(
                    [
                        {"id": "1", "scheduledOn": "a", "originatedFrom": "a"},
                        {"id": "2", "scheduledOn": "b", "originatedFrom": "a"},
                    ]
                ),
                encoding="utf-8",
            )
            d = evaluate_multinode_from_workloads(path)
            self.assertTrue(d["ok"])
            self.assertTrue(d["multinode"])

    def test_missing_file(self) -> None:
        d = evaluate_multinode_from_workloads(Path("/tmp/does-not-exist-pair-wl.json"))
        self.assertFalse(d["ok"])
        self.assertEqual(d["reason"], "workloads_history_missing")

    def test_upstream_constant(self) -> None:
        self.assertIn("NVIDIA/Personal-AI-Router", UPSTREAM_GITHUB)
        self.assertTrue(str(default_workloads_history_path()).endswith("workloads-history.json"))


if __name__ == "__main__":
    unittest.main()
