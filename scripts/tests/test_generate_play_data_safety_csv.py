from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from scripts import generate_play_data_safety_csv as gen


ROOT = Path(__file__).resolve().parents[2]


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


def _source_fixture(repo_root: Path) -> Path:
    source = json.loads((ROOT / "marketing/compliance/play_data_safety_source.json").read_text(encoding="utf-8"))
    evidence_paths = set(source["policy_basis"])
    for data_type in source["data_types"]:
        evidence_paths.update(data_type["evidence"])
    for evidence_path in evidence_paths:
        target = repo_root / evidence_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("test evidence\n", encoding="utf-8")

    source_path = repo_root / "marketing/compliance/play_data_safety_source.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(json.dumps(source), encoding="utf-8")
    return source_path


def test_generator_patches_official_template_shape(tmp_path: Path) -> None:
    source = _source_fixture(tmp_path)
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
        repo_root=tmp_path,
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


def test_generator_accepts_local_template_with_bom(tmp_path: Path) -> None:
    source = _source_fixture(tmp_path)
    template = tmp_path / "template.csv"
    output = tmp_path / "play_data_safety.csv"
    evidence = tmp_path / "evidence.json"
    template.write_text("\ufeff" + _template(), encoding="utf-8")

    result = gen.generate(
        source_path=source,
        output_path=output,
        evidence_path=evidence,
        template_path=template,
        template_url="",
        repo_root=tmp_path,
    )

    assert result["status"] == "generated"
    assert result["selected_data_type_count"] == 5
    assert output.read_text(encoding="utf-8").startswith(gen.CSV_COLUMNS[0])


def test_generator_reports_remote_template_fetch_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_urlopen(*_args: object, **_kwargs: object) -> object:
        raise gen.urllib.error.URLError("timed out")

    monkeypatch.setattr(gen.urllib.request, "urlopen", fail_urlopen)

    try:
        gen._load_template(None, "https://example.invalid/play-data-safety.csv")
    except SystemExit as exc:
        message = str(exc)
        assert "Failed to fetch Play Data Safety CSV template" in message
        assert "example.invalid" in message
        assert "timed out" in message
    else:
        raise AssertionError("Expected remote template fetch failure to exit cleanly")


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
            repo_root=tmp_path,
        )
    except SystemExit as exc:
        assert "missing evidence" in str(exc).lower()
    else:
        raise AssertionError("Expected missing evidence to fail")


def test_generator_rejects_output_path_outside_repo(tmp_path: Path) -> None:
    source = _source_fixture(tmp_path)
    template = tmp_path / "template.csv"
    template.write_text(_template(), encoding="utf-8")

    try:
        gen.generate(
            source_path=source,
            output_path=tmp_path.parent / "outside.csv",
            evidence_path=tmp_path / "evidence.json",
            template_path=template,
            template_url="",
            repo_root=tmp_path,
        )
    except SystemExit as exc:
        assert "inside repo root" in str(exc)
    else:
        raise AssertionError("Expected outside output path to fail")
