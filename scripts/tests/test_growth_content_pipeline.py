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

    def test_add_utm_preserves_existing_query_and_supports_content_override(self):
        url = pipeline.add_utm(
            "https://example.com/path?platform=ios",
            "x",
            "daily_blog_20260219",
            content="2026-02-19-sample",
        )
        self.assertIn("platform=ios", url)
        self.assertIn("utm_source=x", url)
        self.assertIn("utm_content=2026-02-19-sample", url)

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
            self.assertIn("Start the 7-day challenge", index_text)
            self.assertIn("Train reaction under stress", index_text)
            self.assertTrue((root / "site" / "llms.txt").is_file())
            self.assertTrue((root / "site" / "agents.md").is_file())
            self.assertTrue((root / "site" / "md" / "2026-02-19-sample.md").is_file())
            self.assertTrue((root / "site" / "download" / "index.html").is_file())

    def test_build_site_renders_privacy_policy_page_and_legacy_alias(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            output_root = repo / "marketing"
            (output_root / "posts").mkdir(parents=True, exist_ok=True)
            (output_root / "diagrams").mkdir(parents=True, exist_ok=True)
            (repo / "PRIVACY_POLICY.md").write_text(
                "# Privacy Policy\n\nWe do not sell your data.\n",
                encoding="utf-8",
            )

            with patch.dict("os.environ", {"BLOG_BASE_URL": "https://example.com/app"}, clear=False):
                pipeline.build_site(output_root)

            canonical_page = (output_root / "site" / "privacy-policy" / "index.html").read_text(encoding="utf-8")
            legacy_page = (output_root / "site" / "PRIVACY_POLICY" / "index.html").read_text(encoding="utf-8")
            sitemap = (output_root / "site" / "sitemap.xml").read_text(encoding="utf-8")
            llms = (output_root / "site" / "llms.txt").read_text(encoding="utf-8")

            self.assertIn("Privacy Policy", canonical_page)
            self.assertIn("We do not sell your data.", canonical_page)
            self.assertEqual(canonical_page, legacy_page)
            self.assertIn("https://example.com/app/privacy-policy/", sitemap)
            self.assertIn("https://example.com/app/PRIVACY_POLICY/", sitemap)
            self.assertIn("https://example.com/app/privacy-policy/", llms)

    def test_build_site_writes_social_meta_structured_data_and_robots(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "posts").mkdir(parents=True, exist_ok=True)
            (root / "diagrams").mkdir(parents=True, exist_ok=True)
            (root / "posts" / "2026-02-19-sample.md").write_text(
                "---\n"
                "title: Sample\n"
                "description: Desc\n"
                "date: 2026-02-19\n"
                "tags: [ai, mobile]\n"
                "---\n\n"
                "## Body\n",
                encoding="utf-8",
            )
            (root / "diagrams" / "2026-02-19-sample.svg").write_text("<svg></svg>", encoding="utf-8")

            with patch.dict("os.environ", {"BLOG_BASE_URL": "https://example.com/blog"}, clear=False):
                pipeline.build_site(root)

            post_html = (root / "site" / "posts" / "2026-02-19-sample.html").read_text(encoding="utf-8")
            index_html = (root / "site" / "index.html").read_text(encoding="utf-8")
            robots = (root / "site" / "robots.txt").read_text(encoding="utf-8")
            self.assertIn('property="og:title"', post_html)
            self.assertIn('name="twitter:card"', post_html)
            self.assertIn('application/ld+json', post_html)
            self.assertIn('rel="canonical"', post_html)
            self.assertIn('property="og:type" content="website"', index_html)
            self.assertIn("Random Tactical Timer | Train Reaction Under Stress", index_html)
            self.assertIn("Sitemap: https://example.com/blog/sitemap.xml", robots)

    def test_build_site_prefers_png_social_image_for_cards_when_available(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            root = repo / "marketing"
            (root / "posts").mkdir(parents=True, exist_ok=True)
            (root / "diagrams").mkdir(parents=True, exist_ok=True)
            (repo / "screenshots").mkdir(parents=True, exist_ok=True)
            (root / "posts" / "2026-02-19-sample.md").write_text(
                "---\n"
                "title: Sample\n"
                "description: Desc\n"
                "date: 2026-02-19\n"
                "tags: [ai, mobile]\n"
                "---\n\n"
                "## Body\n",
                encoding="utf-8",
            )
            (root / "diagrams" / "2026-02-19-sample.svg").write_text("<svg></svg>", encoding="utf-8")
            (repo / "screenshots" / "ios-active.png").write_bytes(b"png")

            with patch.dict("os.environ", {"BLOG_BASE_URL": "https://example.com/blog"}, clear=False):
                pipeline.build_site(root)

            post_html = (root / "site" / "posts" / "2026-02-19-sample.html").read_text(encoding="utf-8")
            self.assertIn("https://example.com/blog/assets/social-preview.png", post_html)
            self.assertTrue((root / "site" / "assets" / "social-preview.png").is_file())

    def test_build_site_creates_smart_download_page(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "posts").mkdir(parents=True, exist_ok=True)
            (root / "diagrams").mkdir(parents=True, exist_ok=True)
            (root / "posts" / "2026-02-19-sample.md").write_text(
                "---\n"
                "title: Sample\n"
                "description: Desc\n"
                "date: 2026-02-19\n"
                "tags: [ai, mobile]\n"
                "---\n\n"
                "## Body\n",
                encoding="utf-8",
            )
            (root / "diagrams" / "2026-02-19-sample.svg").write_text("<svg></svg>", encoding="utf-8")

            with patch.dict("os.environ", {"BLOG_BASE_URL": "https://example.com/blog"}, clear=False):
                summary = pipeline.build_site(root)

            download_html = (root / "site" / "download" / "index.html").read_text(encoding="utf-8")
            self.assertEqual(summary["download_url"], "https://example.com/blog/download")
            self.assertIn("randomtimer://open", download_html)
            self.assertIn("Continue to App Store", download_html)
            self.assertIn("Continue to Google Play", download_html)
            self.assertIn("window.location.replace(deepLink)", download_html)

    def test_build_site_mirrors_public_pages_for_marketing_output(self):
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            marketing_root = repo_root / "marketing"
            (marketing_root / "posts").mkdir(parents=True, exist_ok=True)
            (marketing_root / "diagrams").mkdir(parents=True, exist_ok=True)
            (repo_root / "PRIVACY_POLICY.md").write_text(
                "# Privacy Policy\n\nWe do not sell your data.\n",
                encoding="utf-8",
            )
            (marketing_root / "posts" / "2026-02-19-sample.md").write_text(
                "---\n"
                "title: Sample\n"
                "description: Desc\n"
                "date: 2026-02-19\n"
                "tags: [ai, mobile]\n"
                "---\n\n"
                "## Body\n",
                encoding="utf-8",
            )
            (marketing_root / "diagrams" / "2026-02-19-sample.svg").write_text("<svg></svg>", encoding="utf-8")

            with patch.dict("os.environ", {"BLOG_BASE_URL": "https://example.com/app"}, clear=False):
                summary = pipeline.build_site(marketing_root)

            self.assertEqual(summary["public_root"], str(repo_root))
            self.assertTrue((repo_root / "index.html").is_file())
            self.assertTrue((repo_root / "download" / "index.html").is_file())
            self.assertTrue((repo_root / "posts" / "2026-02-19-sample.html").is_file())
            self.assertTrue((repo_root / "styles.css").is_file())

            public_index = (repo_root / "index.html").read_text(encoding="utf-8")
            public_download = (repo_root / "download" / "index.html").read_text(encoding="utf-8")
            self.assertIn("Start the 7-day challenge", public_index)
            self.assertIn("randomtimer://open", public_download)
            self.assertIn("Continue to App Store", public_download)

    def test_resolve_public_site_base_url_strips_legacy_marketing_segment(self):
        with tempfile.TemporaryDirectory() as td:
            output_root = Path(td) / "marketing"
            output_root.mkdir(parents=True, exist_ok=True)

            with patch.dict("os.environ", {}, clear=True):
                self.assertEqual(
                    pipeline.resolve_public_site_base_url(output_root),
                    "https://igorganapolsky.github.io/Random-Timer",
                )

    def test_build_site_renders_privacy_policy_page_and_legacy_alias(self):
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            marketing_root = repo_root / "marketing"
            (marketing_root / "posts").mkdir(parents=True, exist_ok=True)
            (marketing_root / "diagrams").mkdir(parents=True, exist_ok=True)
            (marketing_root / "posts" / "2026-02-19-sample.md").write_text(
                "---\n"
                "title: Sample\n"
                "description: Desc\n"
                "date: 2026-02-19\n"
                "tags: [ai, mobile]\n"
                "---\n\n"
                "## Body\n",
                encoding="utf-8",
            )
            (marketing_root / "diagrams" / "2026-02-19-sample.svg").write_text("<svg></svg>", encoding="utf-8")
            (repo_root / "PRIVACY_POLICY.md").write_text("# Privacy Policy\n\nWe respect your data.\n", encoding="utf-8")

            with patch.dict("os.environ", {"BLOG_BASE_URL": "https://example.com/marketing/site"}, clear=False):
                pipeline.build_site(marketing_root)

            canonical_page = (marketing_root / "site" / "privacy-policy" / "index.html").read_text(encoding="utf-8")
            legacy_page = (marketing_root / "site" / "PRIVACY_POLICY" / "index.html").read_text(encoding="utf-8")
            sitemap = (marketing_root / "site" / "sitemap.xml").read_text(encoding="utf-8")
            llms = (marketing_root / "site" / "llms.txt").read_text(encoding="utf-8")

            self.assertIn("Privacy Policy", canonical_page)
            self.assertIn("We respect your data.", canonical_page)
            self.assertEqual(canonical_page, legacy_page)
            self.assertIn("https://example.com/privacy-policy/", sitemap)
            self.assertIn("https://example.com/PRIVACY_POLICY/", sitemap)
            self.assertIn("https://example.com/privacy-policy/", llms)

    def test_publish_post_uses_channel_specific_utm_links(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "posts").mkdir(parents=True, exist_ok=True)
            (root / "diagrams").mkdir(parents=True, exist_ok=True)
            (root / "data").mkdir(parents=True, exist_ok=True)

            md = root / "posts" / "2026-02-21-sample.md"
            md.write_text(
                "---\n"
                "title: Sample\n"
                "description: Desc\n"
                "date: 2026-02-21\n"
                "tags: [ai, testing]\n"
                "---\n\n"
                "## Body\n",
                encoding="utf-8",
            )
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

            with patch.dict("os.environ", {"BLOG_BASE_URL": "https://example.com/blog"}, clear=False):
                with patch.object(
                    pipeline,
                    "_post_devto",
                    return_value={"channel": "devto", "status": "published", "url": "https://dev.to/x"},
                ) as mocked_devto:
                    with patch.object(
                        pipeline,
                        "_post_linkedin",
                        return_value={"channel": "linkedin", "status": "published"},
                    ) as mocked_linkedin:
                        with patch.object(
                            pipeline,
                            "_post_x",
                            return_value={"channel": "x", "status": "published"},
                        ) as mocked_x:
                            pipeline.publish_post(post, root, dry_run=False, devto_mode="control")

            devto_url = mocked_devto.call_args[0][3]
            linkedin_url = mocked_linkedin.call_args[0][1]
            x_url = mocked_x.call_args[0][1]
            self.assertEqual(devto_url, "https://example.com/blog/posts/2026-02-21-sample.html")
            self.assertIn("utm_source=linkedin", linkedin_url)
            self.assertIn("utm_source=x", x_url)
            self.assertIn("utm_content=2026-02-21-sample", x_url)

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
            "https://igorganapolsky.github.io/Random-Timer",
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
