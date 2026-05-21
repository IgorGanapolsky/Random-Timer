from __future__ import annotations

from scripts.check_ios_version_lineage import evaluate_lineage


def test_evaluate_lineage_rejects_local_marketing_version_behind_remote():
    report = evaluate_lineage(
        bundle_id="com.igorganapolsky.randomtimer",
        local_version="1.2.6",
        local_build=172,
        remote_versions=["1.0", "1.2.6", "1.3.9"],
        remote_app_store_versions={},
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
        remote_app_store_versions={},
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
        remote_app_store_versions={},
        remote_builds_by_version={"1.3.9": [409]},
    )

    assert report.passed is True
    assert report.highest_remote_version == "1.3.9"


def test_evaluate_lineage_rejects_closed_app_store_train_even_when_pre_release_matches():
    report = evaluate_lineage(
        bundle_id="com.igorganapolsky.randomtimer",
        local_version="1.3.17",
        local_build=434,
        remote_versions=["1.3.17"],
        remote_app_store_versions={"1.3.17": "READY_FOR_DISTRIBUTION"},
        remote_builds_by_version={"1.3.17": [435]},
    )

    assert report.passed is False
    assert report.highest_closed_app_store_version == "1.3.17"
    assert "distribution-locked" in report.reason
    assert "1.3.17" in report.reason


def test_evaluate_lineage_allows_same_marketing_version_while_waiting_for_review():
    report = evaluate_lineage(
        bundle_id="com.igorganapolsky.randomtimer",
        local_version="1.3.24",
        local_build=449,
        remote_versions=["1.3.24"],
        remote_app_store_versions={"1.3.24": "WAITING_FOR_REVIEW"},
        remote_builds_by_version={"1.3.24": [451]},
    )

    assert report.passed is True
    assert "auto-increment" in report.reason


def test_evaluate_lineage_rejects_local_version_behind_higher_app_store_version():
    report = evaluate_lineage(
        bundle_id="com.igorganapolsky.randomtimer",
        local_version="1.3.17",
        local_build=434,
        remote_versions=["1.3.17"],
        remote_app_store_versions={"1.3.18": "PREPARE_FOR_SUBMISSION"},
        remote_builds_by_version={"1.3.17": [435]},
    )

    assert report.passed is False
    assert report.highest_remote_version == "1.3.18"
    assert "regresses behind App Store Connect version 1.3.18" in report.reason
