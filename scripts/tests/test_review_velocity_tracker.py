from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.review_velocity_tracker as tracker


class ReviewVelocityTrackerTests(unittest.TestCase):
    def test_fetch_ios_reads_cache_when_present(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache_dir = root / "marketing" / "data"
            cache_dir.mkdir(parents=True)
            (cache_dir / "asc_reviews_cache.json").write_text(
                json.dumps({"total_count": 4, "avg_rating": 4.5, "recent_7d": 1}),
                encoding="utf-8",
            )
            result = tracker.fetch_ios_reviews_count(root)
            self.assertEqual(result, {"total_reviews": 4, "avg_rating": 4.5, "recent_count": 1})

    def test_fetch_ios_falls_back_to_itunes_api_when_cache_missing(self):
        """When no ASC cache exists, fall back to the public iTunes Search API
        so the tracker reports real numbers instead of a silent zero placeholder."""
        fake_response = {
            "resultCount": 1,
            "results": [{
                "userRatingCount": 1,
                "averageUserRating": 5.0,
                "bundleId": "com.igorganapolsky.randomtimer",
            }],
        }

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.object(tracker, "_lookup_itunes", return_value=fake_response):
                result = tracker.fetch_ios_reviews_count(root)

        self.assertEqual(result["total_reviews"], 1)
        self.assertEqual(result["avg_rating"], 5.0)
        self.assertEqual(result["recent_count"], 0)

    def test_fetch_ios_returns_zero_when_itunes_lookup_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.object(tracker, "_lookup_itunes", return_value=None):
                result = tracker.fetch_ios_reviews_count(root)
            self.assertEqual(result, {"total_reviews": 0, "avg_rating": 0.0, "recent_count": 0})

    def test_fetch_android_reads_cache_when_present(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache_dir = root / "marketing" / "data"
            cache_dir.mkdir(parents=True)
            (cache_dir / "play_reviews_cache.json").write_text(
                json.dumps({"total_count": 2, "avg_rating": 4.0, "recent_7d": 1}),
                encoding="utf-8",
            )
            result = tracker.fetch_android_reviews_count(root)
            self.assertEqual(result, {"total_reviews": 2, "avg_rating": 4.0, "recent_count": 1})

    def test_fetch_android_falls_back_to_play_scraper_when_cache_missing(self):
        """Mirror of the iOS fallback. Captures real reviews like Lana Karpel's
        5-star from 2026-03-29 that Play Store's aggregate API suppresses below
        its display threshold."""
        fake_reviews = [
            {"score": 5, "userName": "Lana Karpel", "at": "2026-03-29 15:42:50"},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.object(tracker, "_lookup_play_reviews", return_value=fake_reviews):
                result = tracker.fetch_android_reviews_count(root)
        self.assertEqual(result["total_reviews"], 1)
        self.assertEqual(result["avg_rating"], 5.0)
        self.assertEqual(result["recent_count"], 0)

    def test_fetch_android_averages_multiple_review_scores(self):
        fake_reviews = [
            {"score": 5, "at": "2026-03-29 15:42:50"},
            {"score": 3, "at": "2026-04-15 09:10:00"},
            {"score": 4, "at": "2026-05-01 12:00:00"},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.object(tracker, "_lookup_play_reviews", return_value=fake_reviews):
                result = tracker.fetch_android_reviews_count(root)
        self.assertEqual(result["total_reviews"], 3)
        self.assertEqual(result["avg_rating"], 4.0)

    def test_fetch_android_returns_zero_when_scraper_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.object(tracker, "_lookup_play_reviews", return_value=None):
                result = tracker.fetch_android_reviews_count(root)
            self.assertEqual(result, {"total_reviews": 0, "avg_rating": 0.0, "recent_count": 0})


if __name__ == "__main__":
    unittest.main()
