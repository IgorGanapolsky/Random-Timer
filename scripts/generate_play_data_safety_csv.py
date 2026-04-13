#!/usr/bin/env python3
"""Generate Google Play Data Safety CSV from repo-owned evidence.

The generator patches Google's official sample/export CSV shape instead of
inventing a private format. That keeps CI deterministic while preserving the
machine-readable question and response IDs expected by Play Console imports and
the Android Publisher `applications.dataSafety` endpoint.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import socket
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
DEFAULT_SOURCE = REPO_ROOT / "marketing" / "compliance" / "play_data_safety_source.json"
DEFAULT_OUTPUT = REPO_ROOT / "marketing" / "compliance" / "play_data_safety.csv"
DEFAULT_EVIDENCE = REPO_ROOT / "marketing" / "compliance" / "play_data_safety_evidence.json"
DEFAULT_TEMPLATE_URL = "https://storage.googleapis.com/support-kms-prod/b5v9It2EgwrgyY1gPFVB3jPUypc5lL3oNg2G"

CSV_COLUMNS = [
    "Question ID (machine readable)",
    "Response ID (machine readable)",
    "Response value",
    "Answer requirement",
    "Human-friendly question label",
]

DATA_TYPE_IDS = {
    "app_activity_app_interactions": ("PSL_DATA_TYPES_APP_ACTIVITY", "PSL_USER_INTERACTION"),
    "app_info_and_performance_crash_logs": ("PSL_DATA_TYPES_APP_PERFORMANCE", "PSL_CRASH_LOGS"),
    "app_info_and_performance_diagnostics": ("PSL_DATA_TYPES_APP_PERFORMANCE", "PSL_PERFORMANCE_DIAGNOSTICS"),
    "device_or_other_ids_device_or_other_ids": ("PSL_DATA_TYPES_IDENTIFIERS", "PSL_DEVICE_ID"),
    "financial_info_purchase_history": ("PSL_DATA_TYPES_FINANCIAL", "PSL_PURCHASE_HISTORY"),
}

PURPOSE_IDS = {
    "app_functionality": "PSL_APP_FUNCTIONALITY",
    "analytics": "PSL_ANALYTICS",
    "developer_communications": "PSL_DEVELOPER_COMMUNICATIONS",
    "fraud_prevention_security": "PSL_FRAUD_PREVENTION_SECURITY",
    "advertising": "PSL_ADVERTISING",
    "personalization": "PSL_PERSONALIZATION",
    "account_management": "PSL_ACCOUNT_MANAGEMENT",
}

TOP_LEVEL_QUESTIONS = {
    "collects": "PSL_DATA_COLLECTION_COLLECTS_PERSONAL_DATA",
    "encrypted": "PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT",
    "deletion": "PSL_DATA_COLLECTION_USER_REQUEST_DELETE",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_within_repo(path: Path, repo_root: Path, label: str) -> Path:
    candidate = (repo_root / path if not path.is_absolute() else path).resolve()
    if not candidate.is_relative_to(repo_root):
        raise SystemExit(f"{label} must resolve inside repo root: {path}")
    return candidate


def _load_template(path: Path | None, url: str) -> str:
    if path:
        return path.read_text(encoding="utf-8-sig")
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            return response.read().decode("utf-8-sig")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        raise SystemExit(f"Failed to fetch Play Data Safety CSV template from {url}: {exc}") from exc


def _read_rows(csv_text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise SystemExit("Play Data Safety CSV template is empty or missing a header row")
    if reader.fieldnames != CSV_COLUMNS:
        raise SystemExit(
            "Unexpected Play Data Safety CSV columns: "
            f"expected={CSV_COLUMNS!r} actual={reader.fieldnames!r}"
        )
    return [
        {column: (row.get(column) or "") for column in CSV_COLUMNS}
        for row in reader
    ]


def _write_rows(rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _response_value(row: dict[str, str]) -> str:
    return row["Response value"].strip().upper()


def _row_key(row: dict[str, str]) -> tuple[str, str]:
    return (
        row["Question ID (machine readable)"],
        row["Response ID (machine readable)"],
    )


def _usage_question(response_id: str, suffix: str) -> str:
    return f"PSL_DATA_USAGE_RESPONSES:{response_id}:{suffix}"


def _selected_data_types(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for item in source.get("data_types", []):
        data_id = str(item.get("id") or "").strip()
        if data_id not in DATA_TYPE_IDS:
            raise SystemExit(f"Unsupported Play Data Safety data type id: {data_id}")
        if item.get("collected") or item.get("shared"):
            selected[data_id] = item
    return selected


def _validate_evidence(source: dict[str, Any], repo_root: Path) -> list[str]:
    missing: list[str] = []
    for path in source.get("policy_basis", []):
        if not (repo_root / str(path)).exists():
            missing.append(str(path))
    for item in source.get("data_types", []):
        for path in item.get("evidence", []):
            if not (repo_root / str(path)).exists():
                missing.append(str(path))
    return sorted(set(missing))


def apply_source_to_template(rows: list[dict[str, str]], source: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    selected = _selected_data_types(source)
    selected_responses = {
        DATA_TYPE_IDS[data_id][1]: item
        for data_id, item in selected.items()
    }
    selected_type_rows = {
        DATA_TYPE_IDS[data_id]
        for data_id in selected
    }

    for row in rows:
        question_id, response_id = _row_key(row)
        if question_id.startswith("PSL_DATA_"):
            row["Response value"] = ""
        if question_id == TOP_LEVEL_QUESTIONS["collects"]:
            row["Response value"] = "TRUE" if selected else "FALSE"
        elif question_id == TOP_LEVEL_QUESTIONS["encrypted"]:
            encrypted = bool(source.get("security_practices", {}).get("encrypts_data_in_transit"))
            row["Response value"] = "TRUE" if encrypted else "FALSE"
        elif question_id == TOP_LEVEL_QUESTIONS["deletion"]:
            deletion = bool(source.get("security_practices", {}).get("supports_data_deletion_request"))
            row["Response value"] = "TRUE" if deletion else "FALSE"
        elif (question_id, response_id) in selected_type_rows:
            row["Response value"] = "TRUE"

    row_index = {_row_key(row): row for row in rows}
    for response_id, item in selected_responses.items():
        collected = bool(item.get("collected"))
        shared = bool(item.get("shared"))
        ephemeral = bool(item.get("ephemeral"))
        required = bool(item.get("required"))
        purposes = {PURPOSE_IDS[p] for p in item.get("purposes", []) if p in PURPOSE_IDS}

        collected_row = row_index.get(
            (_usage_question(response_id, "PSL_DATA_USAGE_COLLECTION_AND_SHARING"), "PSL_DATA_USAGE_ONLY_COLLECTED")
        )
        shared_row = row_index.get(
            (_usage_question(response_id, "PSL_DATA_USAGE_COLLECTION_AND_SHARING"), "PSL_DATA_USAGE_ONLY_SHARED")
        )
        ephemeral_row = row_index.get((_usage_question(response_id, "PSL_DATA_USAGE_EPHEMERAL"), ""))
        optional_row = row_index.get(
            (_usage_question(response_id, "DATA_USAGE_USER_CONTROL"), "PSL_DATA_USAGE_USER_CONTROL_OPTIONAL")
        )
        required_row = row_index.get(
            (_usage_question(response_id, "DATA_USAGE_USER_CONTROL"), "PSL_DATA_USAGE_USER_CONTROL_REQUIRED")
        )

        for label, found in {
            "collected": collected_row,
            "shared": shared_row,
            "ephemeral": ephemeral_row,
            "optional": optional_row,
            "required": required_row,
        }.items():
            if found is None:
                raise SystemExit(f"Template missing usage row for {response_id}: {label}")

        collected_row["Response value"] = "TRUE" if collected else ""
        shared_row["Response value"] = "TRUE" if shared else ""
        ephemeral_row["Response value"] = "TRUE" if ephemeral else "FALSE"
        optional_row["Response value"] = "" if required else "TRUE"
        required_row["Response value"] = "TRUE" if required else ""

        for purpose_id in PURPOSE_IDS.values():
            collection_row = row_index.get(
                (_usage_question(response_id, "DATA_USAGE_COLLECTION_PURPOSE"), purpose_id)
            )
            sharing_row = row_index.get(
                (_usage_question(response_id, "DATA_USAGE_SHARING_PURPOSE"), purpose_id)
            )
            if collection_row is not None:
                collection_row["Response value"] = "TRUE" if purpose_id in purposes and collected else ""
            if sharing_row is not None:
                sharing_row["Response value"] = "TRUE" if purpose_id in purposes and shared else ""

    evidence = {
        "status": "generated",
        "package_name": source.get("package_name"),
        "selected_data_type_count": len(selected),
        "selected_data_type_ids": sorted(selected),
        "selected_response_ids": sorted(selected_responses),
        "true_response_count": sum(1 for row in rows if _response_value(row) == "TRUE"),
        "false_response_count": sum(1 for row in rows if _response_value(row) == "FALSE"),
        "negative_claims": source.get("negative_claims", {}),
        "security_practices": source.get("security_practices", {}),
    }
    return rows, evidence


def generate(
    *,
    source_path: Path,
    output_path: Path,
    evidence_path: Path,
    template_path: Path | None,
    template_url: str,
    repo_root: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    source_path = _resolve_within_repo(source_path, repo_root, "source_path")
    output_path = _resolve_within_repo(output_path, repo_root, "output_path")
    evidence_path = _resolve_within_repo(evidence_path, repo_root, "evidence_path")
    template_path = _resolve_within_repo(template_path, repo_root, "template_path") if template_path else None

    source = _load_json(source_path)
    missing_evidence = _validate_evidence(source, repo_root)
    if missing_evidence:
        raise SystemExit(f"Play Data Safety source references missing evidence files: {missing_evidence}")

    template = _load_template(template_path, template_url)
    rows = _read_rows(template)
    patched_rows, evidence = apply_source_to_template(rows, source)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_write_rows(patched_rows), encoding="utf-8")
    evidence.update(
        {
            "source_path": str(source_path.relative_to(repo_root) if source_path.is_relative_to(repo_root) else source_path),
            "output_path": str(output_path.relative_to(repo_root) if output_path.is_relative_to(repo_root) else output_path),
            "evidence_path": str(evidence_path.relative_to(repo_root) if evidence_path.is_relative_to(repo_root) else evidence_path),
            "template_url": template_url if template_path is None else "",
            "template_path": str(template_path) if template_path else "",
            "row_count": len(patched_rows),
        }
    )
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")  # NOSONAR - validated by _resolve_within_repo.
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Play Data Safety CSV from repo evidence")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--evidence-output", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--template-path", type=Path, default=None)
    parser.add_argument("--template-url", default=DEFAULT_TEMPLATE_URL)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--json-stdout", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    result = generate(
        source_path=args.source,
        output_path=args.output,
        evidence_path=args.evidence_output,
        template_path=args.template_path,
        template_url=args.template_url,
        repo_root=repo_root,
    )
    if args.json_stdout:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"generated {result['output_path']} rows={result['row_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
