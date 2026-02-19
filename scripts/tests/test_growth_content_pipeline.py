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


if __name__ == "__main__":
    unittest.main()
