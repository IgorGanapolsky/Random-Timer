import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.delegation_contract import evaluate_contract


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "delegation_contract.py"


def _valid_asc_payload() -> dict:
    checks = []

    for name in (
        "App Store Version Exists",
        "Privacy Policy URL",
        "App Review Contact",
        "Pricing Set",
        "Age Rating Completed",
    ):
        checks.append({"name": name, "passed": True, "details": "OK", "evidence": {}})

    checks.append(
        {
            "name": "Build Attached",
            "passed": True,
            "details": "build=25 processingState=VALID",
            "evidence": {"buildNumber": "25", "processingState": "VALID"},
        }
    )
    checks.append(
        {
            "name": "Localization Metadata",
            "passed": True,
            "details": "locale=en-US OK",
            "evidence": {
                "locale": "en-US",
                "description_len": 120,
                "keywords_len": 32,
                "supportUrl": "https://example.com/support",
            },
        }
    )
    screenshot_evidence = {
        "complete_counts": {
            "APP_IPHONE_69": 4,
            "APP_IPAD_PRO_13": 3,
        },
        "total_counts": {
            "APP_IPHONE_69": 4,
            "APP_IPAD_PRO_13": 3,
        },
        "state_counts": {
            "APP_IPHONE_69": {"COMPLETE": 4},
            "APP_IPAD_PRO_13": {"COMPLETE": 3},
        },
        "incomplete_assets": {},
    }
    checks.append(
        {
            "name": "Screenshots (iPhone)",
            "passed": True,
            "details": "need >= 3 COMPLETE in a large iPhone set",
            "evidence": screenshot_evidence,
        }
    )
    checks.append(
        {
            "name": "Screenshots (iPad)",
            "passed": True,
            "details": "need >= 3 COMPLETE in a large iPad set",
            "evidence": screenshot_evidence,
        }
    )

    return {"app_id": "12345", "checks": checks}


class DelegationContractTests(unittest.TestCase):
    def test_ios_metadata_sync_passes_for_ready_context(self):
        report = evaluate_contract(
            operation="ios_metadata_sync",
            context_payload={"summary": {"local_ready": True, "blockers": []}},
            intent=True,
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["blockers"], [])

    def test_ios_metadata_sync_fails_when_local_not_ready(self):
        report = evaluate_contract(
            operation="ios_metadata_sync",
            context_payload={"summary": {"local_ready": False, "blockers": ["local_listing_requirements_failed"]}},
            intent=True,
        )
        self.assertFalse(report["passed"])
        self.assertIn("Local Listing Requirements", report["blockers"])

    def test_ios_submit_for_review_requires_explicit_intent(self):
        report = evaluate_contract(
            operation="ios_submit_for_review",
            asc_ready_payload=_valid_asc_payload(),
            intent=False,
        )
        self.assertFalse(report["passed"])
        self.assertIn("Explicit Human Intent", report["blockers"])

    def test_ios_submit_for_review_fails_without_required_check(self):
        payload = _valid_asc_payload()
        payload["checks"] = [item for item in payload["checks"] if item["name"] != "Pricing Set"]

        report = evaluate_contract(
            operation="ios_submit_for_review",
            asc_ready_payload=payload,
            intent=True,
        )
        self.assertFalse(report["passed"])
        self.assertIn("Pricing Set", report["blockers"])

    def test_ios_submit_for_review_fails_on_invalid_build_state(self):
        payload = _valid_asc_payload()
        for item in payload["checks"]:
            if item["name"] == "Build Attached":
                item["evidence"]["processingState"] = "PROCESSING"
                item["details"] = "build=25 processingState=PROCESSING"

        report = evaluate_contract(
            operation="ios_submit_for_review",
            asc_ready_payload=payload,
            intent=True,
        )
        self.assertFalse(report["passed"])
        self.assertIn("Build Evidence Integrity", report["blockers"])

    def test_cli_enforce_returns_nonzero_on_contract_failure(self):
        payload = _valid_asc_payload()
        with tempfile.TemporaryDirectory() as td:
            asc_json = Path(td) / "asc.json"
            asc_json.write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--operation",
                    "ios_submit_for_review",
                    "--asc-ready-json",
                    str(asc_json),
                    "--intent",
                    "false",
                    "--enforce",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
