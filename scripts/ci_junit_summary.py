#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any


def _case_status(case: ET.Element) -> str:
    if case.findall("error"):
        return "error"
    if case.findall("failure"):
        return "failed"
    if case.findall("skipped"):
        return "skipped"
    return "passed"


def _message(case: ET.Element) -> str:
    for tag in ("error", "failure", "skipped"):
        node = case.find(tag)
        if node is not None:
            message = node.attrib.get("message") or (node.text or "")
            return " ".join(message.split())[:500]
    return ""


def _annotation_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _read_cases(path: Path) -> list[dict[str, Any]]:
    root = ET.parse(path).getroot()
    cases: list[dict[str, Any]] = []
    for case in root.iter("testcase"):
        classname = case.attrib.get("classname", "")
        name = case.attrib.get("name", "")
        status = _case_status(case)
        cases.append(
            {
                "classname": classname,
                "name": name,
                "status": status,
                "time": float(case.attrib.get("time") or 0.0),
                "message": _message(case),
                "file": str(path),
            }
        )
    return cases


def _expand_patterns(patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        for match in glob.glob(pattern, recursive=True):
            path = Path(match)
            if path.is_file():
                paths.add(path)
    return sorted(paths)


def summarize(patterns: list[str]) -> dict[str, Any]:
    files = _expand_patterns(patterns)
    parse_errors: list[dict[str, str]] = []
    cases: list[dict[str, Any]] = []

    for path in files:
        try:
            cases.extend(_read_cases(path))
        except ET.ParseError as exc:
            parse_errors.append({"file": str(path), "error": str(exc)})

    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    by_key: dict[tuple[str, str], set[str]] = defaultdict(set)
    for case in cases:
        status = case["status"]
        counts[status] += 1
        by_key[(case["classname"], case["name"])].add(status)

    failed_cases = [case for case in cases if case["status"] in {"failed", "error"}]
    flaky_candidates = [
        {
            "classname": classname,
            "name": name,
            "statuses": sorted(statuses),
        }
        for (classname, name), statuses in sorted(by_key.items())
        if "passed" in statuses and ({"failed", "error"} & statuses)
    ]

    return {
        "files": len(files),
        "tests": len(cases),
        "passed": counts["passed"],
        "failures": counts["failed"],
        "errors": counts["error"],
        "skipped": counts["skipped"],
        "failed_cases": failed_cases,
        "flaky_candidates": flaky_candidates,
        "parse_errors": parse_errors,
        "status": "failed" if failed_cases or parse_errors else "passed",
    }


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# JUnit Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| XML files | {summary['files']} |",
        f"| Tests | {summary['tests']} |",
        f"| Passed | {summary['passed']} |",
        f"| Failures | {summary['failures']} |",
        f"| Errors | {summary['errors']} |",
        f"| Skipped | {summary['skipped']} |",
        f"| Flaky candidates | {len(summary['flaky_candidates'])} |",
        "",
    ]

    if summary["failed_cases"]:
        lines.extend(["## Failed Cases", ""])
        for case in summary["failed_cases"]:
            label = f"{case['classname']}.{case['name']}".strip(".")
            message = f" - {case['message']}" if case.get("message") else ""
            lines.append(f"- `{case['status']}` `{label}` in `{case['file']}`{message}")
        lines.append("")

    if summary["flaky_candidates"]:
        lines.extend(["## Flaky Candidates", ""])
        for case in summary["flaky_candidates"]:
            label = f"{case['classname']}.{case['name']}".strip(".")
            statuses = ", ".join(case["statuses"])
            lines.append(f"- `{label}` had mixed statuses: `{statuses}`")
        lines.append("")

    if summary["parse_errors"]:
        lines.extend(["## Parse Errors", ""])
        for err in summary["parse_errors"]:
            lines.append(f"- `{err['file']}`: {err['error']}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def emit_annotations(summary: dict[str, Any]) -> None:
    for case in summary["failed_cases"]:
        label = f"{case['classname']}.{case['name']}".strip(".")
        detail = case.get("message") or "JUnit reported a test failure."
        print(f"::error title=JUnit {case['status']}::{_annotation_escape(label + ' - ' + detail)}")

    for case in summary["flaky_candidates"]:
        label = f"{case['classname']}.{case['name']}".strip(".")
        statuses = ", ".join(case["statuses"])
        print(f"::warning title=Flaky test candidate::{_annotation_escape(label + ' had mixed statuses: ' + statuses)}")

    for err in summary["parse_errors"]:
        print(f"::error title=JUnit parse error::{_annotation_escape(err['file'] + ': ' + err['error'])}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize JUnit XML into CI evidence artifacts.")
    parser.add_argument("patterns", nargs="+", help="JUnit XML glob pattern(s).")
    parser.add_argument("--json-out", required=True, help="Path to write summary JSON.")
    parser.add_argument("--markdown-out", required=True, help="Path to write summary Markdown.")
    parser.add_argument("--require-files", action="store_true", help="Fail if no XML files match.")
    parser.add_argument("--github-annotations", action="store_true", help="Emit GitHub workflow annotations.")
    args = parser.parse_args()

    summary = summarize(args.patterns)
    json_path = Path(args.json_out)
    markdown_path = Path(args.markdown_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(summary, markdown_path)

    if args.github_annotations:
        emit_annotations(summary)

    print(
        "JUnit summary: "
        f"files={summary['files']} tests={summary['tests']} failures={summary['failures']} "
        f"errors={summary['errors']} skipped={summary['skipped']} "
        f"flaky_candidates={len(summary['flaky_candidates'])}"
    )

    if args.require_files and summary["files"] == 0:
        print("No JUnit XML files matched required patterns.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
