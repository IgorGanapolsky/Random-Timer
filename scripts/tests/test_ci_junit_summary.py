from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.ci_junit_summary import summarize


def _write_junit(path: Path, body: str) -> None:
    path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite tests="1">
{body}
</testsuite>
""",
        encoding="utf-8",
    )


def test_summary_counts_failures_errors_skips_and_flake_candidates(tmp_path: Path) -> None:
    _write_junit(
        tmp_path / "TEST-first.xml",
        """
  <testcase classname="TimerTests" name="stablePass"/>
  <testcase classname="TimerTests" name="stableFail"><failure message="boom"/></testcase>
  <testcase classname="TimerTests" name="flaky"><failure message="first run"/></testcase>
  <testcase classname="TimerTests" name="skipped"><skipped message="not relevant"/></testcase>
""",
    )
    _write_junit(
        tmp_path / "TEST-second.xml",
        """
  <testcase classname="TimerTests" name="flaky"/>
  <testcase classname="TimerTests" name="errored"><error message="crash"/></testcase>
""",
    )

    summary = summarize([str(tmp_path / "TEST-*.xml")])

    assert summary["files"] == 2
    assert summary["tests"] == 6
    assert summary["passed"] == 2
    assert summary["failures"] == 2
    assert summary["errors"] == 1
    assert summary["skipped"] == 1
    assert summary["status"] == "failed"
    assert summary["flaky_candidates"] == [
        {"classname": "TimerTests", "name": "flaky", "statuses": ["failed", "passed"]}
    ]


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    _write_junit(tmp_path / "TEST-one.xml", '<testcase classname="TimerTests" name="works"/>')
    json_out = tmp_path / "summary.json"
    markdown_out = tmp_path / "summary.md"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ci_junit_summary.py",
            str(tmp_path / "TEST-*.xml"),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
            "--github-annotations",
            "--require-files",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "JUnit summary: files=1 tests=1" in result.stdout
    assert json.loads(json_out.read_text(encoding="utf-8"))["status"] == "passed"
    assert "| Tests | 1 |" in markdown_out.read_text(encoding="utf-8")


def test_require_files_returns_nonzero_when_missing(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ci_junit_summary.py",
            str(tmp_path / "missing-*.xml"),
            "--json-out",
            str(tmp_path / "summary.json"),
            "--markdown-out",
            str(tmp_path / "summary.md"),
            "--require-files",
        ],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "No JUnit XML files matched" in result.stderr
