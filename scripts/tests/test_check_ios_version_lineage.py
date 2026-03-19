from __future__ import annotations

from scripts.check_ios_version_lineage import evaluate_lineage


def test_evaluate_lineage_rejects_local_marketing_version_behind_remote():
    report = evaluate_lineage(
        bundle_id="com.igorganapolsky.randomtimer",
        local_version="1.2.6",
        local_build=172,
        remote_versions=["1.0", "1.2.6", "1.3.9"],
        remote_builds_by_version={"1.2.6": [194], "1.3.9": [409]},
    )

    assert report.passed is False
    assert report.highest_remote_version == "1.3.9"
    assert report.highest_remote_build_for_highest_version == 409
    assert "regresses behind" in report.reason


def test_evaluate_lineage_allows_current_marketing_version_with_lower_local_build():
    report = evaluate_lineage(
        bundle_id="com.igorganapolsky.randomtimer",
        local_version="1.3.9",
        local_build=409,
        remote_versions=["1.0", "1.2.6", "1.3.9"],
        remote_builds_by_version={"1.2.6": [194], "1.3.9": [409]},
    )

    assert report.passed is True
    assert report.highest_remote_version == "1.3.9"
    assert report.highest_remote_build_for_local_version == 409
    assert "lineage_is_current" in report.reason or "auto-increment" in report.reason


def test_evaluate_lineage_ignores_non_semver_remote_versions_when_choosing_highest():
    report = evaluate_lineage(
        bundle_id="com.igorganapolsky.randomtimer",
        local_version="1.3.9",
        local_build=409,
        remote_versions=["1.0", "1.3.9", "not-a-version"],
        remote_builds_by_version={"1.3.9": [409]},
    )

    assert report.passed is True
    assert report.highest_remote_version == "1.3.9"
