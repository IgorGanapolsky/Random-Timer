import json
import tempfile
import unittest
from pathlib import Path

from scripts import sentry_incident_sync as sis


class SentryIncidentSyncTests(unittest.TestCase):
    def setUp(self):
        self.fixture = (
            Path(__file__).resolve().parent / "fixtures" / "sentry_incident_sync_issues.json"
        )

    def _config(self, **overrides):
        base = sis.Config(
            sentry_org="max-smith-kdp-llc",
            sentry_project="apps",
            sentry_auth_token="token",
            github_repo="IgorGanapolsky/Random-Timer",
            github_token="gh-token",
            lookback_days=7,
            min_events=5,
            min_users=2,
            max_issues=20,
            dry_run=True,
            issues_json=self.fixture,
            json_out=None,
        )
        return sis.Config(**{**base.__dict__, **overrides})

    def test_classify_issue_ignores_qa_menu_noise(self):
        issues = sis.fetch_sentry_issues(self._config())
        classification = sis.classify_issue(issues[1], self._config())

        self.assertFalse(classification["eligible"])
        self.assertIn("ignored:qa menu", classification["reasons"])

    def test_classify_issue_promotes_monetization_incident(self):
        issues = sis.fetch_sentry_issues(self._config())
        classification = sis.classify_issue(issues[0], self._config())

        self.assertTrue(classification["eligible"])
        self.assertEqual(classification["priority"], "high")
        self.assertEqual(classification["area"], "monetization")

    def test_run_dry_run_reports_create_action_for_eligible_issue(self):
        result = sis.run(self._config(github_token=""))

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"]["fetched"], 2)
        self.assertEqual(result["summary"]["eligible"], 1)
        actions = [action for action in result["actions"] if action["short_id"] == "RANDOM-TIMER-101"]
        self.assertEqual(actions[0]["action"], "would_create")

    def test_run_skips_when_required_configuration_is_missing(self):
        result = sis.run(self._config(sentry_org="", github_repo="", github_token="", sentry_auth_token="", issues_json=None))

        self.assertEqual(result["status"], "skipped_missing_config")
        self.assertTrue(result["warnings"])

    def test_run_closes_stale_incidents_when_sentry_issue_disappears(self):
        calls = []

        def fake_list_open_synced_issues(repo, token):
            return [
                {
                    "number": 99,
                    "title": "Sentry Incident: [HIGH] RANDOM-TIMER-999 Old incident",
                    "body": "<!-- sentry-incident-sync:org=max-smith-kdp-llc;project=apps;issue=RANDOM-TIMER-999 -->\nold body",
                }
            ]

        def fake_close_issue(repo, token, number, comment):
            calls.append((repo, number, comment))

        def fake_create_issue(repo, token, title, body):
            return 101

        original_list = sis.list_open_synced_issues
        original_close = sis.close_issue
        original_ensure = sis.ensure_labels
        original_create = sis.create_issue
        try:
            sis.list_open_synced_issues = fake_list_open_synced_issues
            sis.close_issue = fake_close_issue
            sis.ensure_labels = lambda repo, token: None
            sis.create_issue = fake_create_issue
            result = sis.run(self._config(dry_run=False))
        finally:
            sis.list_open_synced_issues = original_list
            sis.close_issue = original_close
            sis.ensure_labels = original_ensure
            sis.create_issue = original_create

        self.assertEqual(result["summary"]["closed"], 1)
        self.assertEqual(calls[0][1], 99)

    def test_main_writes_json_report(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.json"
            config = self._config(github_token="", json_out=out)
            result = sis.run(config)
            out.write_text(json.dumps(result, indent=2, default=sis._json_default) + "\n", encoding="utf-8")

            self.assertTrue(out.exists())
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["eligible"], 1)


if __name__ == "__main__":
    unittest.main()
