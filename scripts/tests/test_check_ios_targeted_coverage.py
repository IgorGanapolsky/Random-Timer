from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.check_ios_targeted_coverage import load_coverages


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_ios_targeted_coverage.py"


def test_load_coverages_walks_nested_targets_and_files(tmp_path: Path):
    report = tmp_path / "xccov.json"
    report.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "name": "RandomTimer",
                        "files": [
                            {
                                "path": "/tmp/RandomTimer/Sources/App/AppBootstrap.swift",
                                "lineCoverage": 1.0,
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    coverages = load_coverages(report)

    assert coverages["/tmp/RandomTimer/Sources/App/AppBootstrap.swift"] == 1.0


def test_cli_fails_when_target_file_is_below_threshold(tmp_path: Path):
    report = tmp_path / "xccov.json"
    report.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "files": [
                            {
                                "path": "/tmp/RandomTimer/Sources/App/AppBootstrap.swift",
                                "lineCoverage": 0.8,
                            }
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--report-json",
            str(report),
            "--require",
            "Sources/App/AppBootstrap.swift=1.0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "below required 100.0%" in result.stdout


def test_cli_passes_when_target_file_meets_threshold(tmp_path: Path):
    report = tmp_path / "xccov.json"
    report.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "files": [
                            {
                                "path": "/tmp/RandomTimer/Sources/App/AppBootstrap.swift",
                                "lineCoverage": 1.0,
                            }
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--report-json",
            str(report),
            "--require",
            "Sources/App/AppBootstrap.swift=1.0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "iOS targeted coverage check passed." in result.stdout
