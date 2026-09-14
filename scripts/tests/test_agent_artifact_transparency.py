"""TDD: compaction-safe artifact vault + tool-trace transparency (Willison Astra)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.agent_artifact_transparency import (
    ALLOWED_CDN_HOSTS,
    FLEET_MONTHLY_CAP_USD,
    compact_session,
    evaluate_platform,
    evaluate_transparency,
    persist_run_artifacts,
    recall_pre_compaction,
    render_share_html,
    validate_cdn_url,
)


class PlatformTests(unittest.TestCase):
    def test_transparency_platform_allowed(self) -> None:
        d = evaluate_platform(platform="artifact_transparency")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_artifact_transparency")

    def test_opaque_chat_only_blocked(self) -> None:
        d = evaluate_platform(platform="opaque_chat_only_agent")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_opaque_chat_only")


class TransparencyGateTests(unittest.TestCase):
    def test_claim_without_recoverable_code_fails(self) -> None:
        d = evaluate_transparency(
            tool_trace_present=True,
            generated_code_persisted=False,
            downloadable_artifacts=("route.geojson",),
            narrative_only_explanation=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unrecoverable_code")

    def test_full_transparency_passes(self) -> None:
        d = evaluate_transparency(
            tool_trace_present=True,
            generated_code_persisted=True,
            downloadable_artifacts=("route.gpx", "route.geojson", "share.html"),
            narrative_only_explanation=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_transparent_artifacts")


class CompactionVaultTests(unittest.TestCase):
    def test_pre_compaction_text_and_code_remain_recallable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            persisted = persist_run_artifacts(
                vault_root=root,
                run_id="astra-5k",
                tool_trace=[
                    {"tool": "nominatim", "query": "address"},
                    {"tool": "overpass", "query": "roads"},
                    {"tool": "local_compute", "query": "loop_5k"},
                ],
                generated_code="print('route')\n",
                artifacts={
                    "route.geojson": '{"type":"LineString","coordinates":[[0,0],[1,1]]}',
                    "notes.txt": "local OSM loop",
                },
                pre_compaction_text="full transcript before compact",
            )
            self.assertTrue(persisted["ok"])

            # Simulate compaction dropping live transcript.
            compact_session(vault_root=root, run_id="astra-5k")

            recalled = recall_pre_compaction(vault_root=root, run_id="astra-5k")
            self.assertTrue(recalled["ok"])
            self.assertEqual(recalled["pre_compaction_text"], "full transcript before compact")
            self.assertIn("print('route')", recalled["generated_code"])
            self.assertEqual(len(recalled["tool_trace"]), 3)
            self.assertTrue((root / "astra-5k" / "route.geojson").exists())

    def test_recall_missing_run_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recalled = recall_pre_compaction(vault_root=Path(tmp), run_id="missing")
            self.assertFalse(recalled["ok"])
            self.assertEqual(recalled["action"], "block_missing_vault_run")


class VisualizeShareTests(unittest.TestCase):
    def test_share_html_embeds_json_and_allowlisted_cdn(self) -> None:
        html = render_share_html(
            title="El Granada harbor loop",
            subtitle="5.1 km",
            data={"route": {"type": "LineString", "coordinates": [[-122.46, 37.49]]}},
            attribution="Map data © OpenStreetMap contributors",
            cdn_script="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js",
        )
        self.assertIn('type="application/json"', html)
        self.assertIn("eg-share-data", html)
        self.assertIn("El Granada harbor loop", html)
        self.assertIn("cdn.jsdelivr.net", html)

    def test_non_allowlisted_cdn_rejected(self) -> None:
        d = validate_cdn_url(url="https://evil.example/d3.js")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_cdn_not_allowlisted")
        for host in (
            "cdn.jsdelivr.net",
            "cdnjs.cloudflare.com",
            "esm.sh",
            "unpkg.com",
        ):
            self.assertIn(host, ALLOWED_CDN_HOSTS)

    def test_render_rejects_bad_cdn(self) -> None:
        with self.assertRaises(ValueError):
            render_share_html(
                title="x",
                subtitle="y",
                data={"a": 1},
                attribution="z",
                cdn_script="https://evil.example/x.js",
            )


class FleetCapTests(unittest.TestCase):
    def test_fleet_cap(self) -> None:
        self.assertEqual(FLEET_MONTHLY_CAP_USD, 20.0)


if __name__ == "__main__":
    unittest.main()
