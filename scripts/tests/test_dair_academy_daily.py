"""TDD: DAIR Academy daily scrape → rank → implement queue."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.dair_academy_daily import build_report, rank_papers, score_text, slug_to_title
from scripts.dair_academy_gate import HEALTH_SIGNALS, evaluate, evaluate_learn_claim


class SlugTests(unittest.TestCase):
    def test_slug_to_title(self) -> None:
        self.assertEqual(
            slug_to_title("/papers/procedural-graphs-2026-09-07-september-13-1"),
            "Procedural Graphs",
        )


class ScoreTests(unittest.TestCase):
    def test_agents_md_scores_high(self) -> None:
        score, hits = score_text("Does AGENTS.md help coding agents context file")
        self.assertGreaterEqual(score, 8)
        self.assertIn("agents.md", hits)


class RankTests(unittest.TestCase):
    def test_rank_extracts_papers(self) -> None:
        html = (
            '<a href="/papers/procedural-graphs-2026-09-07-september-13-1">x</a>'
            "procedural long-horizon agents graph "
            '<a href="/papers/frognano-2026-09-07-september-13-2">y</a>'
        )
        ranked = rank_papers(html, "https://academy.dair.ai/papers/week/x")
        titles = [row["title"] for row in ranked]
        self.assertIn("Procedural Graphs", titles)
        self.assertGreaterEqual(len(ranked), 1)


class BuildReportTests(unittest.TestCase):
    def test_extras_enter_queue(self) -> None:
        papers = '<a href="/papers/week/2026-09-07-september-13">w</a>'
        week = (
            '<a href="/papers/procedural-graphs-2026-09-07-september-13-1">p</a>'
            "procedural graph long-horizon agent"
        )
        report = build_report(
            papers_html=papers,
            week_html=week,
            extras=[
                {
                    "title": "Does AGENTS.md Actually Help Coding Agents?",
                    "url": "https://academy.dair.ai/dashboard/resources/agents-md-evaluation",
                    "summary": "human AGENTS.md context file coding agent benchmark",
                }
            ],
        )
        self.assertGreaterEqual(report["paper_count"], 1)
        self.assertTrue(report["implement_queue"])
        titles = [item["title"] for item in report["implement_queue"]]
        self.assertTrue(any("AGENTS.md" in title for title in titles))


class GateClaimTests(unittest.TestCase):
    def test_paid_unlock_blocked(self) -> None:
        d = evaluate_learn_claim({"action": "academy_paid_unlock"})
        self.assertFalse(d.ok)

    def test_llm_agents_md_blocked(self) -> None:
        d = evaluate_learn_claim({"action": "auto_generate_agents_md"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_llm_agents_md_bloat")

    def test_scrape_with_tests_allowed(self) -> None:
        d = evaluate_learn_claim({"action": "scrape_and_rank", "tests_planned": True})
        self.assertTrue(d.ok)


class GatePresenceTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertEqual(len(HEALTH_SIGNALS), 4)

    def test_missing_docs_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = evaluate(Path(tmp))
            self.assertFalse(report["ready"])
            self.assertIn("missing_docs/DAIR_ACADEMY_DAILY.md", report["blockers"])

    def test_empty_artifact_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "DAIR_ACADEMY_DAILY.md").write_text(
                "papers roi implement agents.md cron paid\n", encoding="utf-8"
            )
            (root / "scripts").mkdir()
            (root / "scripts" / "dair_academy_daily.py").write_text("#\n")
            (root / "scripts" / "dair_academy_gate.py").write_text("#\n")
            wf = root / ".github" / "workflows"
            wf.mkdir(parents=True)
            (wf / "dair-academy-daily.yml").write_text("name: x\n")
            for sr in (".cursor/skills", ".claude/skills"):
                p = root / sr / "dair-academy-daily"
                p.mkdir(parents=True)
                (p / "SKILL.md").write_text("# dair-academy-daily\n")
            fixture = root / "marketing" / "data" / "code_health"
            fixture.mkdir(parents=True)
            (fixture / "dair_academy_discipline.json").write_text(
                json.dumps(
                    {
                        "daily_scrape_papers": True,
                        "rank_by_wqtu_profit_roi": "x",
                        "queue_implementable_steals": "y",
                        "human_agents_md_not_llm_bloat": "z",
                    }
                )
            )
            (root / "marketing" / "data" / "dair_daily_learn.json").write_text("{}\n")
            report = evaluate(root)
            self.assertFalse(report["ready"])
            self.assertTrue(any("artifact_" in b or "artifact_empty" in b for b in report["blockers"]))

    def test_wired_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "DAIR_ACADEMY_DAILY.md").write_text(
                "\n".join(
                    [
                        "# DAIR",
                        "papers roi implement agents.md cron paid unlocks skipped",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "scripts").mkdir()
            (root / "scripts" / "dair_academy_daily.py").write_text("#\n")
            (root / "scripts" / "dair_academy_gate.py").write_text("#\n")
            wf = root / ".github" / "workflows"
            wf.mkdir(parents=True)
            (wf / "dair-academy-daily.yml").write_text("name: x\n")
            for sr in (".cursor/skills", ".claude/skills"):
                p = root / sr / "dair-academy-daily"
                p.mkdir(parents=True)
                (p / "SKILL.md").write_text("# dair-academy-daily\n")
            fixture = root / "marketing" / "data" / "code_health"
            fixture.mkdir(parents=True)
            (fixture / "dair_academy_discipline.json").write_text(
                json.dumps(
                    {
                        "daily_scrape_papers": True,
                        "rank_by_wqtu_profit_roi": "x",
                        "queue_implementable_steals": "y",
                        "human_agents_md_not_llm_bloat": "z",
                    }
                )
            )
            (root / "marketing" / "data" / "dair_daily_learn.json").write_text(
                json.dumps({
                    "framework": "dair-academy-daily",
                    "scraped_at_utc": "2026-09-15T18:42:47Z",
                    "paper_count": 1,
                    "papers": [{"title": "Procedural Graphs"}],
                    "implement_queue": [],
                })
                + "\n"
            )
            report = evaluate(root)
            self.assertTrue(report["ready"], msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
