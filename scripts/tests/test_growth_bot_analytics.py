import json
import tempfile
import unittest
from pathlib import Path

import scripts.growth_bot_analytics as bots


class GrowthBotAnalyticsTests(unittest.TestCase):
    def test_classify_user_agent(self):
        row = bots.classify_user_agent("Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)")
        self.assertEqual(row["bot_type"], "ai_training")
        self.assertEqual(row["model"], "openai")

    def test_analyze_logs_aggregates_counts(self):
        summary = bots.analyze_logs(
            [
                {"user_agent": "GPTBot/1.0", "path": "/pricing"},
                {"user_agent": "PerplexityBot/1.0", "path": "/pricing"},
                {"user_agent": "Mozilla/5.0", "path": "/"},
            ]
        )
        self.assertEqual(summary["total_ai_bot_hits"], 2)
        self.assertEqual(summary["bot_types"]["ai_training"], 1)
        self.assertEqual(summary["bot_types"]["ai_retrieval"], 1)

    def test_run_writes_reports(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "access-log.ndjson"
            input_path.write_text(
                "\n".join(
                    [
                        json.dumps({"user_agent": "GPTBot/1.0", "path": "/index"}),
                        json.dumps({"user_agent": "Googlebot/2.1", "path": "/blog"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            payload = bots.run(input_path, root)
            self.assertEqual(payload["status"], "ok")
            self.assertTrue((root / "bot_traffic_summary.json").is_file())
            self.assertTrue((root / "bot_traffic_summary.md").is_file())


if __name__ == "__main__":
    unittest.main()
