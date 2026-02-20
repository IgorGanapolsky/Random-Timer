import json
import tempfile
import unittest
from pathlib import Path

import scripts.growth_keyword_engine as engine


class GrowthKeywordEngineTests(unittest.TestCase):
    def test_expand_keywords_contains_seed_and_modifier_forms(self):
        rows = engine.expand_keywords(["random timer"], ["best", "for beginners"])
        self.assertIn("random timer", rows)
        self.assertIn("best random timer", rows)
        self.assertIn("random timer for beginners", rows)

    def test_build_backlog_scores_and_flags(self):
        blueprint = {
            "seed_keywords": ["random timer"],
            "modifiers": ["best", "what is", "calculator"],
        }
        backlog = engine.build_backlog(blueprint, max_keywords=20)
        self.assertGreaterEqual(len(backlog), 3)
        self.assertTrue(any(item["tool_keyword"] for item in backlog))
        self.assertTrue(any(item["ai_trap"] for item in backlog))

    def test_run_build_writes_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = root / "keywords"
            strategy = root / "strategy.json"
            strategy.write_text(
                json.dumps(
                    {
                        "niche": "x",
                        "monetization": "y",
                        "audience": "z",
                        "seed_keywords": ["random timer"],
                        "modifiers": ["best", "calculator"],
                    }
                ),
                encoding="utf-8",
            )
            payload = engine.run_build(out, strategy)
            self.assertEqual(payload["status"], "ok")
            self.assertTrue((out / "keyword_backlog.json").is_file())
            self.assertTrue((out / "keyword_backlog.csv").is_file())
            self.assertTrue((out / "keyword_backlog.md").is_file())


if __name__ == "__main__":
    unittest.main()
