#!/usr/bin/env python3
"""Validate AI review payloads against the Random Timer review contract.

Enforces:
- Strict schema (verdict, summary, issues)
- File:line evidence per issue
- Maximum unresolved critical issues (default: 0)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any

VERDICTS = {"APPROVE", "REQUEST_CHANGES", "BLOCK"}
SEVERITIES = {"critical", "major", "minor", "style"}
STATUSES = {"open", "fixed", "accepted_risk"}


@dataclass(frozen=True)
class ValidationError:
    path: str
    message: str


def _load_payload(path: pathlib.Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)

    # Support markdown/text artifacts containing fenced JSON.
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if not match:
        raise ValueError("no JSON payload found (expected .json or fenced ```json block)")
    return json.loads(match.group(1))


def _validate_contract(payload: Any, payload_path: str, max_unresolved_critical: int) -> list[ValidationError]:
    errors: list[ValidationError] = []

    if not isinstance(payload, dict):
        return [ValidationError(payload_path, "payload must be a JSON object")]

    allowed_top_keys = {"verdict", "summary", "issues"}
    missing_top = [k for k in ("verdict", "summary", "issues") if k not in payload]
    for key in missing_top:
        errors.append(ValidationError(payload_path, f"missing top-level key: {key}"))

    extra_top = sorted(set(payload.keys()) - allowed_top_keys)
    if extra_top:
        errors.append(ValidationError(payload_path, f"unexpected top-level keys: {', '.join(extra_top)}"))

    verdict = payload.get("verdict")
    if verdict not in VERDICTS:
        errors.append(ValidationError(payload_path, f"verdict must be one of {sorted(VERDICTS)}"))

    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append(ValidationError(payload_path, "summary must be a non-empty string"))

    issues = payload.get("issues")
    if not isinstance(issues, list):
        errors.append(ValidationError(payload_path, "issues must be an array"))
        return errors

    unresolved_critical = 0

    for idx, issue in enumerate(issues):
        issue_path = f"{payload_path}:issues[{idx}]"
        if not isinstance(issue, dict):
            errors.append(ValidationError(issue_path, "issue must be an object"))
            continue

        allowed_issue_keys = {"severity", "status", "file", "line", "description", "suggestion"}
        required_issue_keys = {"severity", "file", "line", "description", "suggestion"}

        for key in sorted(required_issue_keys - set(issue.keys())):
            errors.append(ValidationError(issue_path, f"missing required key: {key}"))

        extra_issue = sorted(set(issue.keys()) - allowed_issue_keys)
        if extra_issue:
            errors.append(ValidationError(issue_path, f"unexpected keys: {', '.join(extra_issue)}"))

        severity = issue.get("severity")
        if severity not in SEVERITIES:
            errors.append(ValidationError(issue_path, f"severity must be one of {sorted(SEVERITIES)}"))

        status = issue.get("status", "open")
        if status not in STATUSES:
            errors.append(ValidationError(issue_path, f"status must be one of {sorted(STATUSES)}"))

        evidence_file = issue.get("file")
        evidence_line = issue.get("line")
        if not isinstance(evidence_file, str) or not evidence_file.strip():
            errors.append(ValidationError(issue_path, "file must be a non-empty string"))
        if not isinstance(evidence_line, int) or evidence_line < 1:
            errors.append(ValidationError(issue_path, "line must be an integer >= 1"))

        description = issue.get("description")
        suggestion = issue.get("suggestion")
        if not isinstance(description, str) or not description.strip():
            errors.append(ValidationError(issue_path, "description must be a non-empty string"))
        if not isinstance(suggestion, str) or not suggestion.strip():
            errors.append(ValidationError(issue_path, "suggestion must be a non-empty string"))

        if severity == "critical" and status != "fixed":
            unresolved_critical += 1

    if unresolved_critical > max_unresolved_critical:
        errors.append(
            ValidationError(
                payload_path,
                f"unresolved critical issues {unresolved_critical} exceed allowed maximum {max_unresolved_critical}",
            )
        )

    return errors


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate AI review artifacts against contract")
    parser.add_argument(
        "--input",
        dest="inputs",
        action="append",
        required=True,
        help="Path to review artifact (.json or markdown with fenced json). Can be provided multiple times.",
    )
    parser.add_argument(
        "--max-unresolved-critical",
        type=int,
        default=0,
        help="Maximum unresolved critical issues allowed before failing the gate (default: 0).",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    all_errors: list[ValidationError] = []

    for raw_input in args.inputs:
        path = pathlib.Path(raw_input)
        if not path.exists():
            all_errors.append(ValidationError(raw_input, "input file does not exist"))
            continue
        try:
            payload = _load_payload(path)
        except Exception as exc:  # noqa: BLE001
            all_errors.append(ValidationError(str(path), f"failed to load payload: {exc}"))
            continue

        all_errors.extend(
            _validate_contract(
                payload=payload,
                payload_path=str(path),
                max_unresolved_critical=args.max_unresolved_critical,
            )
        )

    if all_errors:
        for error in all_errors:
            print(f"[review-contract] {error.path}: {error.message}")
        return 1

    print("[review-contract] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
