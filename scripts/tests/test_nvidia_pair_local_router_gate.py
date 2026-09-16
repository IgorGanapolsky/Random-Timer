"""TDD: NVIDIA PAIR local router lite + fleet scheduler."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.nvidia_pair_fleet import schedule_independent_jobs, select_eligible_node
from scripts.nvidia_pair_local_router_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_pair_claim,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "NVIDIA_PAIR_LOCAL_ROUTER.md").write_text(
        "\n".join(
            [
                "# NVIDIA PAIR",
                "pair proxy ollama lm studio",
                "workload level concurrency independent jobs",
                "eligible engine model ready",
                "jobs telemetry ground truth workloads-history",
                "no vram pooling",
                "tailscale lan pairing",
                "s25 edge ollama hermes",
                "github.com/NVIDIA/Personal-AI-Router ollama-pr",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "nvidia_pair_local_router_gate.py").write_text("#\n")
    (root / "scripts" / "nvidia_pair_fleet.py").write_text("#\n")
    (root / "scripts" / "nvidia_pair_workloads.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "nvidia-pair-local-router-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# nvidia-pair-local-router-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "nvidia_pair_local_router_discipline.json").write_text(
        json.dumps(
            {
                "proxy_familiar_local_interface": True,
                "workload_level_concurrency": True,
                "one_request_one_node": True,
                "elastic_home_nodes": True,
                "eligibility_model_engine_ready": True,
                "jobs_telemetry_ground_truth": True,
                "workloads_history_ground_truth": True,
                "no_vram_pooling": True,
                "no_harness_api_change": True,
                "tailscale_or_lan_pairing": True,
                "s25_edge_ollama_not_native_pair": True,
                "upstream_personal_ai_router_github": True,
                "budget": {"paid_remote_gpu_saas": False},
            }
        )
    )
    fleet = root / "marketing" / "data" / "fleet"
    fleet.mkdir(parents=True)
    (fleet / "nvidia_pair_nodes.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": "macbook-pro",
                        "role": "primary",
                        "native_pair": True,
                        "online": True,
                        "ready": True,
                        "engines": ["ollama"],
                        "models": ["qwen2.5:3b-hermes-64k"],
                        "active_jobs": 0,
                    },
                    {
                        "id": "mac-mini",
                        "role": "spare",
                        "native_pair": True,
                        "online": True,
                        "ready": True,
                        "engines": ["ollama"],
                        "models": ["qwen2.5:3b-hermes-64k"],
                        "active_jobs": 0,
                    },
                    {
                        "id": "galaxy-s25",
                        "role": "edge",
                        "native_pair": False,
                        "online": True,
                        "ready": True,
                        "engines": ["ollama"],
                        "models": ["qwen2.5:3b-hermes-64k"],
                        "active_jobs": 0,
                    },
                ]
            }
        )
    )


def _fleet_two_ready() -> dict:
    return {
        "nodes": [
            {
                "id": "a",
                "online": True,
                "ready": True,
                "engines": ["ollama"],
                "models": ["m"],
                "active_jobs": 0,
                "gpu_util": 0.2,
            },
            {
                "id": "b",
                "online": True,
                "ready": True,
                "engines": ["ollama"],
                "models": ["m"],
                "active_jobs": 0,
                "gpu_util": 0.1,
            },
        ]
    }


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertGreaterEqual(len(HEALTH_SIGNALS), 8)


class FleetTests(unittest.TestCase):
    def test_select_prefers_lower_load(self) -> None:
        fleet = _fleet_two_ready()
        fleet["nodes"][0]["active_jobs"] = 2
        node = select_eligible_node(fleet=fleet, model="m", engine="ollama")
        assert node is not None
        self.assertEqual(node["id"], "b")

    def test_schedule_spreads_across_nodes(self) -> None:
        plan = schedule_independent_jobs(
            fleet=_fleet_two_ready(), model="m", engine="ollama", job_count=4
        )
        self.assertTrue(plan["ok"])
        self.assertTrue(plan["multinode"])
        self.assertEqual(plan["nodes_used"], 2)

    def test_missing_model_blocks(self) -> None:
        plan = schedule_independent_jobs(
            fleet=_fleet_two_ready(), model="missing", engine="ollama", job_count=1
        )
        self.assertFalse(plan["ok"])

    def test_nonpositive_jobs_rejected(self) -> None:
        for n in (0, -3):
            plan = schedule_independent_jobs(
                fleet=_fleet_two_ready(), model="m", engine="ollama", job_count=n
            )
            self.assertFalse(plan["ok"])
            self.assertEqual(plan["reason"], "invalid_job_count")
            self.assertEqual(plan["requested"], n)
            self.assertEqual(plan["placed"], 0)

    def test_fixture_local_offline_until_probe(self) -> None:
        from scripts.nvidia_pair_fleet import apply_live_liveness

        fleet = {
            "proxy_base_url": "http://127.0.0.1:9",
            "nodes": [
                {
                    "id": "macbook-pro",
                    "host": "localhost",
                    "online": True,
                    "ready": True,
                    "engines": ["ollama"],
                    "models": ["m"],
                    "active_jobs": 0,
                }
            ],
        }
        # Fixture says ready, but dead port must flip offline
        live = apply_live_liveness(fleet, timeout_s=0.3)
        self.assertFalse(live["live_probe_ok"])
        self.assertFalse(live["nodes"][0]["online"])
        self.assertFalse(live["nodes"][0]["ready"])
        plan = schedule_independent_jobs(
            fleet=live, model="m", engine="ollama", job_count=1
        )
        self.assertFalse(plan["ok"])


class ClaimTests(unittest.TestCase):
    def test_vram_pool_blocked(self) -> None:
        d = evaluate_pair_claim({"action": "pool_vram"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_vram_pooling_or_shard")

    def test_multinode_without_jobs_blocked(self) -> None:
        d = evaluate_pair_claim({"action": "claim_multinode_without_jobs"})
        self.assertFalse(d.ok)

    def test_s25_native_blocked(self) -> None:
        d = evaluate_pair_claim({"action": "treat_s25_as_native_pair_node"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_s25_native_pair_claim")

    def test_paid_gpu_blocked(self) -> None:
        d = evaluate_pair_claim({"action": "buy_cloud_gpu_cluster"})
        self.assertFalse(d.ok)

    def test_verify_proxy_requires_smoke(self) -> None:
        d = evaluate_pair_claim({"action": "verify_proxy", "proxy_port_ok": True})
        self.assertFalse(d.ok)
        d2 = evaluate_pair_claim(
            {
                "action": "verify_proxy",
                "proxy_port_ok": True,
                "chat_smoke_ok": True,
            }
        )
        self.assertTrue(d2.ok)

    def test_schedule_allowed(self) -> None:
        d = evaluate_pair_claim(
            {
                "action": "schedule",
                "model": "m",
                "engine": "ollama",
                "job_count": 3,
                "fleet": _fleet_two_ready(),
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_scheduled_jobs")


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])
            self.assertEqual(report["framework"], "nvidia-pair-local-router-lite")
            self.assertIn("infoq.com", report["infoq_source"])


if __name__ == "__main__":
    unittest.main()
