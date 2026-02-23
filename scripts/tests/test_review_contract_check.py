import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "review_contract_check.py"
FIXTURES = ROOT / "scripts" / "tests" / "fixtures" / "review_contract"


class ReviewContractCheckTests(unittest.TestCase):
    def run_check(self, *inputs: pathlib.Path, max_unresolved_critical: int = 0) -> subprocess.CompletedProcess[str]:
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--max-unresolved-critical",
            str(max_unresolved_critical),
        ]
        for path in inputs:
            cmd.extend(["--input", str(path)])
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    def test_valid_json_payload_passes(self):
        result = self.run_check(FIXTURES / "valid_review.json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_valid_markdown_fenced_json_passes(self):
        result = self.run_check(FIXTURES / "valid_review.md")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_missing_file_line_evidence_fails(self):
        result = self.run_check(FIXTURES / "invalid_missing_evidence.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required key: line", result.stdout)

    def test_unresolved_critical_fails_gate(self):
        result = self.run_check(FIXTURES / "invalid_unresolved_critical.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unresolved critical issues", result.stdout)

    def test_multiple_inputs_fail_if_any_invalid(self):
        result = self.run_check(
            FIXTURES / "valid_review.json",
            FIXTURES / "invalid_missing_evidence.json",
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
