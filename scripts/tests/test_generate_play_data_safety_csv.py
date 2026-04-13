from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from scripts import generate_play_data_safety_csv as gen


def _row(question: str, response: str = "", requirement: str = "MULTIPLE_CHOICE") -> dict[str, str]:
    return {
        "Question ID (machine readable)": question,
        "Response ID (machine readable)": response,
        "Response value": "",
        "Answer requirement": requirement,
        "Human-friendly question label": question,
    }


def _template() -> str:
    rows: list[dict[str, str]] = [
        _row("PSL_DATA_COLLECTION_COLLECTS_PERSONAL_DATA", requirement="REQUIRED"),
        _row("PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT", requirement="MAYBE_REQUIRED"),
        _row("PSL_DATA_COLLECTION_USER_REQUEST_DELETE", requirement="MAYBE_REQUIRED"),
    ]
    for question, response in gen.DATA_TYPE_IDS.values():
        rows.append(_row(question, response))
        rows.extend(
            [
                _row(gen._usage_question(response, "PSL_DATA_USAGE_COLLECTION_AND_SHARING"), "PSL_DATA_USAGE_ONLY_COLLECTED"),
                _row(gen._usage_question(response, "PSL_DATA_USAGE_COLLECTION_AND_SHARING"), "PSL_DATA_USAGE_ONLY_SHARED"),
                _row(gen._usage_question(response, "PSL_DATA_USAGE_EPHEMERAL"), "", "MAYBE_REQUIRED"),
                _row(gen._usage_question(response, "DATA_USAGE_USER_CONTROL"), "PSL_DATA_USAGE_USER_CONTROL_OPTIONAL", "SINGLE_CHOICE"),
                _row(gen._usage_question(response, "DATA_USAGE_USER_CONTROL"), "PSL_DATA_USAGE_USER_CONTROL_REQUIRED", "SINGLE_CHOICE"),
            ]
        )
        for purpose in gen.PURPOSE_IDS.values():
            rows.append(_row(gen._usage_question(response, "DATA_USAGE_COLLECTION_PURPOSE"), purpose))
            rows.append(_row(gen._usage_question(response, "DATA_USAGE_SHARING_PURPOSE"), purpose))

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=gen.CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def test_generator_patches_official_template_shape(tmp_path: Path) -> None:
    source = Path("marketing/compliance/play_data_safety_source.json").resolve()
    template = tmp_path / "template.csv"
    output = tmp_path / "play_data_safety.csv"
    evidence = tmp_path / "evidence.json"
    template.write_text(_template(), encoding="utf-8")

    result = gen.generate(
        source_path=source,
        output_path=output,
        evidence_path=evidence,
        template_path=template,
        template_url="",
        repo_root=Path.cwd(),
    )

    rows = list(csv.DictReader(io.StringIO(output.read_text(encoding="utf-8"))))
    true_rows = {
        (row["Question ID (machine readable)"], row["Response ID (machine readable)"])
        for row in rows
        if row["Response value"] == "TRUE"
    }

    assert result["selected_data_type_count"] == 5
    assert ("PSL_DATA_TYPES_APP_ACTIVITY", "PSL_USER_INTERACTION") in true_rows
    assert ("PSL_DATA_TYPES_APP_PERFORMANCE", "PSL_CRASH_LOGS") in true_rows
    assert ("PSL_DATA_TYPES_IDENTIFIERS", "PSL_DEVICE_ID") in true_rows
    assert ("PSL_DATA_TYPES_FINANCIAL", "PSL_PURCHASE_HISTORY") in true_rows
    assert json.loads(evidence.read_text(encoding="utf-8"))["negative_claims"]["uses_advertising_id"] is False


def test_generator_rejects_missing_evidence(tmp_path: Path) -> None:
    source = {
        "package_name": "com.example",
        "policy_basis": ["missing-file.md"],
        "security_practices": {},
        "data_types": [],
    }
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    try:
        gen.generate(
            source_path=source_path,
            output_path=tmp_path / "out.csv",
            evidence_path=tmp_path / "evidence.json",
            template_path=tmp_path / "template.csv",
            template_url="",
            repo_root=Path.cwd(),
        )
    except SystemExit as exc:
        assert "missing evidence" in str(exc).lower()
    else:
        raise AssertionError("Expected missing evidence to fail")
