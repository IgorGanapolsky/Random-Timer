import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import scripts.release_ops as release_ops


class ReleaseOpsTests(unittest.TestCase):
    def test_check_readiness_runs_preflight_and_context(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "scripts").mkdir(parents=True, exist_ok=True)
            context_out = repo / "release-context.json"

            calls = []

            def fake_run(cmd, cwd, env=None):
                calls.append((list(cmd), cwd))
                if any(str(x).endswith("release_context.py") for x in cmd):
                    context_out.write_text(
                        json.dumps(
                            {
                                "summary": {
                                    "local_ready": True,
                                    "remote_status": "success",
                                    "sla_breach_count": 0,
                                    "blockers": [],
                                }
                            }
                        ),
                        encoding="utf-8",
                    )
                return subprocess.CompletedProcess(cmd, 0)

            args = SimpleNamespace(
                platform="ios",
                version="1.1.1",
                locale="en-US",
                context_out=str(context_out),
                contract_out=None,
                review_limit=200,
                sla_hours=24,
                strict_remote=True,
                fail_on_sla=False,
                no_remote=False,
                enforce_contract=True,
            )

            with patch.object(release_ops, "_run", side_effect=fake_run):
                rc = release_ops.check_readiness(args, repo)

            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 2)
            self.assertTrue(calls[0][0][1].endswith("preflight-release.sh"))
            self.assertTrue(any(str(x).endswith("release_context.py") for x in calls[1][0]))

    def test_check_readiness_honors_fail_on_sla(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "scripts").mkdir(parents=True, exist_ok=True)
            context_out = repo / "release-context.json"

            def fake_run(cmd, cwd, env=None):
                if any(str(x).endswith("release_context.py") for x in cmd):
                    context_out.write_text(
                        json.dumps(
                            {
                                "summary": {
                                    "local_ready": True,
                                    "remote_status": "success",
                                    "sla_breach_count": 3,
                                    "blockers": ["review_sla_breaches_present"],
                                }
                            }
                        ),
                        encoding="utf-8",
                    )
                return subprocess.CompletedProcess(cmd, 0)

            args = SimpleNamespace(
                platform="ios",
                version="1.1.1",
                locale="en-US",
                context_out=str(context_out),
                contract_out=None,
                review_limit=200,
                sla_hours=24,
                strict_remote=False,
                fail_on_sla=True,
                no_remote=False,
                enforce_contract=True,
            )

            with patch.object(release_ops, "_run", side_effect=fake_run):
                rc = release_ops.check_readiness(args, repo)

            self.assertEqual(rc, 1)

    def test_check_readiness_allows_contract_failure_when_not_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "scripts").mkdir(parents=True, exist_ok=True)
            context_out = repo / "release-context.json"

            def fake_run(cmd, cwd, env=None):
                if any(str(x).endswith("release_context.py") for x in cmd):
                    context_out.write_text(
                        json.dumps(
                            {
                                "summary": {
                                    "local_ready": False,
                                    "remote_status": "skipped_no_remote",
                                    "sla_breach_count": 0,
                                    "blockers": ["local_listing_requirements_failed"],
                                }
                            }
                        ),
                        encoding="utf-8",
                    )
                return subprocess.CompletedProcess(cmd, 0)

            args = SimpleNamespace(
                platform="ios",
                version="1.1.1",
                locale="en-US",
                context_out=str(context_out),
                contract_out=None,
                review_limit=200,
                sla_hours=24,
                strict_remote=False,
                fail_on_sla=False,
                no_remote=False,
                enforce_contract=False,
            )

            with patch.object(release_ops, "_run", side_effect=fake_run):
                rc = release_ops.check_readiness(args, repo)

            self.assertEqual(rc, 0)

    def test_sync_listing_dry_run_skips_execution(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "native-ios").mkdir(parents=True, exist_ok=True)

            args = SimpleNamespace(version="1.1.1", upload_metadata=True, dry_run=True)
            env = {
                "APPSTORE_KEY_ID": "KEY",
                "APPSTORE_ISSUER_ID": "ISSUER",
                "APPSTORE_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch.object(release_ops, "_run") as run_mock:
                    rc = release_ops.sync_listing(args, repo)
            self.assertEqual(rc, 0)
            run_mock.assert_not_called()

    def test_sync_listing_requires_private_key_material(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "native-ios").mkdir(parents=True, exist_ok=True)

            args = SimpleNamespace(version="1.1.1", upload_metadata=True, dry_run=True)
            env = {
                "APPSTORE_KEY_ID": "KEY",
                "APPSTORE_ISSUER_ID": "ISSUER",
                "APPSTORE_PRIVATE_KEY": "",
                "APPSTORE_PRIVATE_KEY_PATH": "",
            }
            with patch.dict(os.environ, env, clear=True):
                rc = release_ops.sync_listing(args, repo)
            self.assertEqual(rc, 2)

    def test_review_autopilot_runs_pipeline_and_appends_history(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "scripts").mkdir(parents=True, exist_ok=True)

            reviews_json = repo / "tmp" / "reviews.json"
            anomaly_json = repo / "tmp" / "anomaly.json"
            policy_json = repo / "tmp" / "policy.json"
            history_jsonl = repo / "tmp" / "history.jsonl"

            def fake_run(cmd, cwd, env=None):
                if any(str(x).endswith("asc_reviews_ops.py") for x in cmd):
                    reviews_json.parent.mkdir(parents=True, exist_ok=True)
                    reviews_json.write_text(
                        json.dumps(
                            {
                                "generatedAt": "2026-02-19T12:00:00+00:00",
                                "averageRating": 4.6,
                                "ratings": {"1": 1, "2": 1, "3": 2, "4": 10, "5": 36},
                                "totalReviews": 50,
                                "unresolvedLowStarCount": 1,
                                "slaBreachCount": 0,
                                "slaBreaches": [],
                            }
                        ),
                        encoding="utf-8",
                    )
                elif any(str(x).endswith("review_anomaly_detector.py") for x in cmd):
                    anomaly_json.parent.mkdir(parents=True, exist_ok=True)
                    anomaly_json.write_text(
                        json.dumps({"status": "ok", "maxSeverity": "none", "score": 0, "anomalies": []}),
                        encoding="utf-8",
                    )
                elif any(str(x).endswith("review_action_policy.py") for x in cmd):
                    policy_json.parent.mkdir(parents=True, exist_ok=True)
                    policy_json.write_text(
                        json.dumps(
                            {
                                "mode": "observe",
                                "anomalyStatus": "ok",
                                "decision": {"route": "MONITOR", "blocking": False, "reasoning": []},
                            }
                        ),
                        encoding="utf-8",
                    )
                return subprocess.CompletedProcess(cmd, 0)

            args = SimpleNamespace(
                limit=200,
                sla_hours=24,
                history_jsonl=str(history_jsonl),
                history_max_lines=2000,
                min_history=8,
                max_age_days=30,
                rating_drop_threshold=0.25,
                low_star_rate_spike_threshold=0.05,
                unresolved_spike_threshold=3.0,
                sla_breach_spike_threshold=1.0,
                mode="observe",
                reviews_json_out=str(reviews_json),
                reviews_markdown_out=None,
                anomaly_json_out=str(anomaly_json),
                anomaly_markdown_out=None,
                policy_json_out=str(policy_json),
                policy_markdown_out=None,
                fail_on_sla=False,
                fail_on_blocking=False,
            )

            with patch.object(release_ops, "_run", side_effect=fake_run):
                rc = release_ops.review_autopilot(args, repo)

            self.assertEqual(rc, 0)
            self.assertTrue(history_jsonl.is_file())
            lines = history_jsonl.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)

    def test_review_autopilot_propagates_policy_failure(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            reviews_json = repo / "reviews.json"
            anomaly_json = repo / "anomaly.json"
            policy_json = repo / "policy.json"
            history_jsonl = repo / "history.jsonl"

            def fake_run(cmd, cwd, env=None):
                if any(str(x).endswith("asc_reviews_ops.py") for x in cmd):
                    reviews_json.write_text(
                        json.dumps(
                            {
                                "generatedAt": "2026-02-19T12:00:00+00:00",
                                "averageRating": 4.1,
                                "ratings": {"1": 5, "2": 4, "3": 6, "4": 10, "5": 25},
                                "totalReviews": 50,
                                "unresolvedLowStarCount": 8,
                                "slaBreachCount": 3,
                                "slaBreaches": [{"id": "r1", "ageHours": 30.0}],
                            }
                        ),
                        encoding="utf-8",
                    )
                    return subprocess.CompletedProcess(cmd, 0)
                if any(str(x).endswith("review_anomaly_detector.py") for x in cmd):
                    anomaly_json.write_text(
                        json.dumps({"status": "alert", "maxSeverity": "high", "score": 20, "anomalies": []}),
                        encoding="utf-8",
                    )
                    return subprocess.CompletedProcess(cmd, 0)
                if any(str(x).endswith("review_action_policy.py") for x in cmd):
                    policy_json.write_text(
                        json.dumps(
                            {
                                "mode": "enforce",
                                "anomalyStatus": "alert",
                                "decision": {
                                    "route": "ESCALATE_HUMAN",
                                    "blocking": True,
                                    "reasoning": ["SLA breaches present"],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return subprocess.CompletedProcess(cmd, 1)
                return subprocess.CompletedProcess(cmd, 0)

            args = SimpleNamespace(
                limit=200,
                sla_hours=24,
                history_jsonl=str(history_jsonl),
                history_max_lines=2000,
                min_history=8,
                max_age_days=30,
                rating_drop_threshold=0.25,
                low_star_rate_spike_threshold=0.05,
                unresolved_spike_threshold=3.0,
                sla_breach_spike_threshold=1.0,
                mode="enforce",
                reviews_json_out=str(reviews_json),
                reviews_markdown_out=None,
                anomaly_json_out=str(anomaly_json),
                anomaly_markdown_out=None,
                policy_json_out=str(policy_json),
                policy_markdown_out=None,
                fail_on_sla=False,
                fail_on_blocking=True,
            )

            with patch.object(release_ops, "_run", side_effect=fake_run):
                rc = release_ops.review_autopilot(args, repo)
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
