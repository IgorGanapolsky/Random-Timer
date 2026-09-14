"""Unit tests for referral content generators beyond SO watchlist."""

from __future__ import annotations

from pathlib import Path


def test_generate_reddit_post_uses_hiit_template() -> None:
    from scripts import backlinks_referral as br

    post = br.generate_reddit_post(
        {"subreddit": "r/HIIT", "audience": "athletes", "angle": "HIIT"},
    )
    assert post["subreddit"] == "r/HIIT"
    assert post["status"] == "draft"
    assert "random" in post["title"].lower() or "HIIT" in post["title"]
    assert "id" in post


def test_generate_reddit_post_default_template() -> None:
    from scripts import backlinks_referral as br

    post = br.generate_reddit_post(
        {"subreddit": "r/unknown", "audience": "x", "angle": "tactical drills"},
    )
    assert "tactical drills" in post["title"]
    assert post["status"] == "draft"


def test_generate_blog_outreach_embeds_angle() -> None:
    from scripts import backlinks_referral as br

    mail = br.generate_blog_outreach(
        {"site": "example.com", "angle": "Boxing coaches love unpredictability"}
    )
    assert mail["status"] == "draft"
    assert "Boxing coaches love unpredictability" in mail["email_template"]


def test_generate_product_hunt_launch_has_checklist(tmp_path: Path) -> None:
    from scripts import backlinks_referral as br

    launch = br.generate_product_hunt_launch(tmp_path)
    assert launch["status"] == "draft"
    assert len(launch["pre_launch_checklist"]) >= 3


def test_build_report_mentions_drafts() -> None:
    from scripts import backlinks_referral as br

    text = br.build_report(
        {
            "timestamp": "2026-09-14T00:00:00Z",
            "reddit_posts": 1,
            "reddit_subreddits": ["r/HIIT"],
            "product_hunt_ready": True,
            "blog_outreach_targets": 2,
            "content_files_generated": 3,
        }
    )
    assert "r/HIIT" in text
    assert "Product Hunt" in text
