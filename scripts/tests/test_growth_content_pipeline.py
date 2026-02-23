import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import scripts.growth_content_pipeline as pipeline


class GrowthContentPipelineTests(unittest.TestCase):
    def test_slugify_normalizes_and_limits(self):
        self.assertEqual(pipeline.slugify("Hello, World!"), "hello-world")
        self.assertEqual(
            pipeline.slugify("A" * 120),
            "a" * 80,
        )

    def test_add_utm_appends_query(self):
        url = pipeline.add_utm("https://example.com/path", "github_pages", "daily_blog_20260219")
        self.assertIn("utm_source=github_pages", url)
        self.assertIn("utm_campaign=daily_blog_20260219", url)

    def test_build_post_copy_includes_inspiration_block_when_supplied(self):
        _, _, body = pipeline.build_post_copy(
            "The inspiration behind Random Tactical Timer",
            ["feat: improve release checks"],
            inspiration_url="https://example.com/inspiration",
        )
        self.assertIn("## Inspiration", body)
        self.assertIn("https://example.com/inspiration", body)

    def test_render_paperbanana_svg_writes_svg(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "diagram.svg"
            pipeline.render_paperbanana_svg(pipeline.paperbanana_diagram_spec(), out)
            text = out.read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            self.assertIn("PaperBanana Tech Flow", text)

    def test_generate_first_post_uses_hard_target_seed_topic(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            out = Path(td) / "marketing"
            repo.mkdir(parents=True, exist_ok=True)

            args = SimpleNamespace(
                repo_root=str(repo),
                output_root=str(out),
                topic="",
                since_days=2,
                max_commits=5,
            )

            with patch.dict(
                "os.environ",
                {
                    "APP_STORE_URL": "https://apps.apple.com/us/app/foo/id1",
                    "PLAY_STORE_URL": "https://play.google.com/store/apps/details?id=foo",
                    "IOS_REVIEW_URL": "https://apps.apple.com/us/app/foo/id1?action=write-review",
                    "ANDROID_REVIEW_URL": "https://play.google.com/store/apps/details?id=foo&reviewId=0",
                },
                clear=False,
            ):
                post = pipeline.generate_post(args)

            text = post.markdown_path.read_text(encoding="utf-8")
            self.assertIn(pipeline.FIRST_POST_TOPIC, text)
            self.assertIn(pipeline.FIRST_POST_SOURCE, text)

    def test_build_site_renders_index(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "posts").mkdir(parents=True, exist_ok=True)
            (root / "diagrams").mkdir(parents=True, exist_ok=True)
            md = root / "posts" / "2026-02-19-sample.md"
            md.write_text(
                "---\n"
                "title: Sample\n"
                "description: Desc\n"
                "date: 2026-02-19\n"
                "tags: [ai, mobile]\n"
                "---\n\n"
                "## Body\n"
                "- point\n",
                encoding="utf-8",
            )
            (root / "diagrams" / "2026-02-19-sample.svg").write_text("<svg></svg>", encoding="utf-8")

            summary = pipeline.build_site(root)
            index_text = (root / "site" / "index.html").read_text(encoding="utf-8")
            self.assertEqual(summary["post_count"], 1)
            self.assertIn("Sample", index_text)
            self.assertTrue((root / "site" / "llms.txt").is_file())
            self.assertTrue((root / "site" / "agents.md").is_file())
            self.assertTrue((root / "site" / "md" / "2026-02-19-sample.md").is_file())

    def test_strip_frontmatter_returns_body_only(self):
        raw = (
            "---\n"
            "title: Sample Post\n"
            "description: Sample Desc\n"
            "---\n\n"
            "## Body\n"
            "- point\n"
        )
        body = pipeline.strip_frontmatter(raw)
        self.assertTrue(body.startswith("## Body"))
        self.assertNotIn("title: Sample Post", body)

    def test_resolve_blog_base_url_defaults_for_marketing_output(self):
        with patch.dict("os.environ", {}, clear=False):
            resolved = pipeline.resolve_blog_base_url(Path("marketing"))
        self.assertEqual(
            resolved,
            "https://igorganapolsky.github.io/Random-Timer/marketing/site",
        )

    def test_resolve_blog_base_url_respects_env_override(self):
        with patch.dict("os.environ", {"BLOG_BASE_URL": "https://example.com/blog/"}, clear=False):
            resolved = pipeline.resolve_blog_base_url(Path("marketing"))
        self.assertEqual(resolved, "https://example.com/blog")

    def test_prepare_devto_markdown_rewrites_diagram_to_absolute_url(self):
        raw = (
            "---\n"
            "title: Sample\n"
            "---\n\n"
            "## Diagram\n"
            "![PaperBanana technology flow](../diagrams/2026-02-19-sample.svg)\n"
        )
        rendered = pipeline.prepare_devto_markdown(
            raw,
            "2026-02-19-sample",
            "https://igorganapolsky.github.io/Random-Timer/marketing/site",
        )
        self.assertIn(
            "https://igorganapolsky.github.io/Random-Timer/marketing/site/diagrams/2026-02-19-sample.svg",
            rendered,
        )
        self.assertNotIn("../diagrams/2026-02-19-sample.svg", rendered)
        self.assertNotIn("title: Sample", rendered)

    def test_choose_ab_arm_balances_runs(self):
        self.assertEqual(pipeline.choose_ab_arm([]), "control")
        self.assertEqual(pipeline.choose_ab_arm([{"arm": "control"}]), "candidate")
        self.assertEqual(
            pipeline.choose_ab_arm([{"arm": "control"}, {"arm": "candidate"}]),
            "control",
        )

    def test_summarize_ab_pilot_requires_all_three_metrics_to_win(self):
        rows = []
        for i in range(7):
            rows.append(
                {
                    "timestamp": f"2026-02-0{i+1}T00:00:00+00:00",
                    "arm": "control",
                    "success": i < 5,
                    "duration_ms": 1000,
                    "estimated_cost_usd": 1.0,
                }
            )
            rows.append(
                {
                    "timestamp": f"2026-02-1{i+1}T00:00:00+00:00",
                    "arm": "candidate",
                    "success": i < 6,
                    "duration_ms": 800,
                    "estimated_cost_usd": 0.6,
                }
            )

        summary = pipeline.summarize_ab_pilot(rows, window_days=14)
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["decision"], "candidate_keep")

    def test_run_publish_ab_pilot_respects_budget_cap(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "posts").mkdir(parents=True, exist_ok=True)
            (root / "diagrams").mkdir(parents=True, exist_ok=True)
            (root / "data").mkdir(parents=True, exist_ok=True)

            md = root / "posts" / "2026-02-21-sample.md"
            md.write_text("---\ntitle: Sample\ndescription: Desc\ndate: 2026-02-21\n---\nbody\n", encoding="utf-8")
            (root / "diagrams" / "2026-02-21-sample.svg").write_text("<svg></svg>", encoding="utf-8")
            (root / "diagrams" / "2026-02-21-sample.mmd").write_text("graph TD;A-->B", encoding="utf-8")

            post = pipeline.PostAsset(
                slug="2026-02-21-sample",
                title="Sample",
                description="Desc",
                created_at="2026-02-21T00:00:00+00:00",
                markdown_path=md,
                diagram_svg_path=root / "diagrams" / "2026-02-21-sample.svg",
                diagram_mermaid_path=root / "diagrams" / "2026-02-21-sample.mmd",
                html_path=root / "site" / "posts" / "2026-02-21-sample.html",
                tags=["ai", "testing"],
            )

            with patch.dict(
                "os.environ",
                {
                    "AB_PILOT_MAX_COST_USD": "0.1",
                    "AB_CONTROL_COST_USD": "0.2",
                    "AB_CANDIDATE_COST_USD": "0.3",
                },
                clear=False,
            ):
                with patch.object(pipeline, "publish_post") as mocked_publish:
                    payload = pipeline.run_publish_ab_pilot(post, root, dry_run=False)
                    mocked_publish.assert_not_called()

            self.assertEqual(payload["run"]["budget_adjustment"], "cap_exhausted")
            self.assertEqual(payload["run"]["status"], "skipped")
            self.assertEqual(payload["summary"]["budget_cap_usd"], 0.1)
            self.assertEqual(payload["summary"]["budget_spent_usd"], 0.0)


if __name__ == "__main__":
    unittest.main()
