import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REVIEWER_SPEC = ROOT / ".claude" / "agents" / "code-reviewer.md"


class CodeReviewerReadOnlyGuardTests(unittest.TestCase):
    def test_reviewer_doc_declares_read_only(self):
        text = REVIEWER_SPEC.read_text(encoding="utf-8")
        self.assertIn("read-only", text.lower())

    def test_allowed_bash_commands_are_read_only(self):
        text = REVIEWER_SPEC.read_text(encoding="utf-8")
        required_safe_commands = ["git diff", "git log", "git show", "cat", "ls", "find"]
        for command in required_safe_commands:
            self.assertIn(command, text, msg=f"Missing required safe command: {command}")

        forbidden_patterns = [
            r"\bgit\s+reset\b",
            r"\bgit\s+checkout\b",
            r"\bgit\s+commit\b",
            r"\bapply_patch\b",
            r"\brm\b",
            r"\bmv\b",
            r"\bchmod\b",
            r"\bchown\b",
            r"\bsed\s+-i\b",
        ]
        lowered = text.lower()
        for pattern in forbidden_patterns:
            self.assertIsNone(
                re.search(pattern, lowered),
                msg=f"Forbidden command leaked into reviewer spec: {pattern}",
            )


if __name__ == "__main__":
    unittest.main()
