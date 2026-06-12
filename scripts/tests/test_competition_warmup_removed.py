from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_FRAGMENTS = (
    "Competition Warmup",
    "Competition Prep",
    "competition_warmup",
    "training_preset_applied",
)

GUARDED_DOC_PATHS = (
    "docs/MONETIZATION_STRATEGY_2026.md",
)

REMOVED_MARKETING_ARTIFACT = "marketing/data/competition_warmup_experiment.md"


def test_competition_warmup_marketing_artifact_removed() -> None:
    assert not (REPO_ROOT / REMOVED_MARKETING_ARTIFACT).exists()


def test_docs_do_not_reference_competition_warmup() -> None:
    for relative_path in GUARDED_DOC_PATHS:
        path = REPO_ROOT / relative_path
        text = path.read_text(encoding="utf-8")
        for fragment in FORBIDDEN_FRAGMENTS:
            assert fragment.lower() not in text.lower(), f"{relative_path} still mentions {fragment!r}"


def test_android_analytics_has_no_training_preset_event() -> None:
    analytics = (
        REPO_ROOT
        / "native-android/app/src/main/java/com/iganapolsky/randomtimer/analytics/AnalyticsService.kt"
    ).read_text(encoding="utf-8")
    assert "TRAINING_PRESET_APPLIED" not in analytics
    assert "PRESET_ID" not in analytics


def test_ios_analytics_has_no_training_preset_event() -> None:
    analytics = (
        REPO_ROOT / "native-ios/RandomTimer/Sources/Services/AnalyticsService.swift"
    ).read_text(encoding="utf-8")
    assert "trainingPresetApplied" not in analytics
    assert "presetId" not in analytics
