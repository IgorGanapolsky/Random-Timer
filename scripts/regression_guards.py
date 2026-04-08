#!/usr/bin/env python3
"""Fast regression guardrails for voice and Play release workflows."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RELEASE_GUARD_PATHS = {
    ".github/workflows/android-production-retry.yml",
    ".github/workflows/native-release.yml",
    "scripts/pre-commit",
    "scripts/regression_guards.py",
    "scripts/source_versions.py",
    "scripts/verify_play_public_listing.py",
    "scripts/tests/test_growth_workflow_contracts.py",
    "scripts/tests/test_regression_guards.py",
    "scripts/tests/test_verify_play_public_listing.py",
}

VOICE_GUARD_PATH_FRAGMENTS = (
    "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/SoundPreviewManagerImpl.kt",
    "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/repository/TimerRepositoryImpl.kt",
    "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/SoundPreviewManager.kt",
    "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimerConfig.kt",
    "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/AIVoiceCalloutManager.kt",
    "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt",
    "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/viewmodel/TimerViewModel.kt",
    "native-ios/RandomTimer/Sources/Services/AIVoiceCalloutService.swift",
    "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift",
    "content/pro_audio/voice_personas.json",
    "scripts/tests/test_mobile_feature_parity.py",
    "scripts/tests/test_voice_regression_contracts.py",
)


def _read(repo_root: Path, relative_path: str) -> str:
    return (repo_root / relative_path).read_text(encoding="utf-8")


def _git_staged_paths(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _normalize_paths(paths: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        path = raw.strip().replace("\\", "/")
        if not path or path in seen:
            continue
        seen.add(path)
        normalized.append(path)
    return normalized


def _matches_voice_path(path: str) -> bool:
    return any(fragment in path for fragment in VOICE_GUARD_PATH_FRAGMENTS)


def _matches_release_path(path: str) -> bool:
    return path in RELEASE_GUARD_PATHS


def relevant_paths(paths: list[str]) -> list[str]:
    return [path for path in _normalize_paths(paths) if _matches_release_path(path) or _matches_voice_path(path)]


def _assert_contains(source: str, needle: str, *, errors: list[str], label: str) -> None:
    if needle not in source:
        errors.append(f"{label}: missing `{needle}`")


def _assert_not_contains(source: str, needle: str, *, errors: list[str], label: str) -> None:
    if needle in source:
        errors.append(f"{label}: unexpected `{needle}`")


def check_android_retry_contract(repo_root: Path, errors: list[str]) -> None:
    source = _read(repo_root, ".github/workflows/android-production-retry.yml")
    label = ".github/workflows/android-production-retry.yml"
    _assert_contains(source, "actions/checkout@v6.0.2", errors=errors, label=label)
    _assert_contains(source, "actions/setup-python@v6.2.0", errors=errors, label=label)
    _assert_contains(
        source,
        "scripts/source_versions.py --format value --key ANDROID_VERSION_NAME",
        errors=errors,
        label=label,
    )
    _assert_contains(
        source,
        "from scripts.verify_play_public_listing import build_store_url, verify_public_listing",
        errors=errors,
        label=label,
    )
    _assert_contains(source, 'build_store_url("com.iganapolsky.randomtimer", "US")', errors=errors, label=label)
    _assert_contains(source, "play_public_current", errors=errors, label=label)
    _assert_contains(source, "play_public_", errors=errors, label=label)
    _assert_not_contains(
        source,
        "ISSUE_TITLE: Android production publish blocked by Play FAILED_PRECONDITION",
        errors=errors,
        label=label,
    )


def check_native_release_contract(repo_root: Path, errors: list[str]) -> None:
    source = _read(repo_root, ".github/workflows/native-release.yml")
    label = ".github/workflows/native-release.yml"
    _assert_contains(source, "require-production-signoff:", errors=errors, label=label)
    _assert_contains(source, "environment: production-signoff", errors=errors, label=label)
    _assert_contains(source, "Await fresh CEO production release approval", errors=errors, label=label)
    _assert_contains(source, "Verify public Google Play listing (production only)", errors=errors, label=label)
    _assert_contains(source, "python scripts/verify_play_public_listing.py", errors=errors, label=label)
    _assert_contains(source, "--expected-version", errors=errors, label=label)
    _assert_contains(source, "steps.versions.outputs.android_version", errors=errors, label=label)


def check_play_public_listing_contract(repo_root: Path, errors: list[str]) -> None:
    source = _read(repo_root, "scripts/verify_play_public_listing.py")
    label = "scripts/verify_play_public_listing.py"
    _assert_contains(source, "expected_version", errors=errors, label=label)
    _assert_contains(source, "VERSION_MISMATCH", errors=errors, label=label)
    _assert_contains(source, "public_version=", errors=errors, label=label)
    _assert_contains(source, "poll_until_visible", errors=errors, label=label)


def check_voice_contract(repo_root: Path, errors: list[str]) -> None:
    android_setup = _read(
        repo_root,
        "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt",
    )
    android_viewmodel = _read(
        repo_root,
        "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/viewmodel/TimerViewModel.kt",
    )
    android_preview = _read(
        repo_root,
        "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/SoundPreviewManager.kt",
    )
    android_preview_impl = _read(
        repo_root,
        "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/SoundPreviewManagerImpl.kt",
    )
    android_repository = _read(
        repo_root,
        "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/repository/TimerRepositoryImpl.kt",
    )
    android_config = _read(
        repo_root,
        "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimerConfig.kt",
    )
    android_voice_manager = _read(
        repo_root,
        "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/AIVoiceCalloutManager.kt",
    )

    _assert_contains(android_setup, "VoiceGender.entries.forEach", errors=errors, label="TimerSetupScreen.kt")
    _assert_contains(android_setup, "onCommandCuePreview(config.voiceGender)", errors=errors, label="TimerSetupScreen.kt")
    _assert_contains(android_setup, '"Male"', errors=errors, label="TimerSetupScreen.kt")
    _assert_contains(android_setup, '"Female"', errors=errors, label="TimerSetupScreen.kt")
    _assert_contains(android_viewmodel, "fun previewCommandCue(gender: VoiceGender)", errors=errors, label="TimerViewModel.kt")
    _assert_contains(android_viewmodel, "trackVoiceGenderSelected", errors=errors, label="TimerViewModel.kt")
    _assert_contains(android_preview, "fun previewCommandCue(gender: VoiceGender)", errors=errors, label="SoundPreviewManager.kt")
    _assert_contains(android_preview_impl, "voiceCalloutManager.previewCommandCue(gender)", errors=errors, label="SoundPreviewManagerImpl.kt")
    _assert_contains(android_repository, 'KEY_VOICE_GENDER = stringPreferencesKey("voice_gender")', errors=errors, label="TimerRepositoryImpl.kt")
    _assert_contains(android_repository, "preferences[KEY_VOICE_GENDER] = config.voiceGender.name", errors=errors, label="TimerRepositoryImpl.kt")
    _assert_contains(android_config, "enum class VoiceGender", errors=errors, label="TimerConfig.kt")
    _assert_contains(android_config, "val voiceGender: VoiceGender = VoiceGender.MALE", errors=errors, label="TimerConfig.kt")
    _assert_contains(android_voice_manager, "VoicePreviewSampleCatalog.femaleCommandFilenames", errors=errors, label="AIVoiceCalloutManager.kt")
    _assert_contains(android_voice_manager, "VoicePreviewSampleCatalog.maleCommandFilenames", errors=errors, label="AIVoiceCalloutManager.kt")
    _assert_contains(android_voice_manager, "fun previewCommandCue(gender: VoiceGender = currentGender)", errors=errors, label="AIVoiceCalloutManager.kt")
    _assert_contains(android_voice_manager, "fun previewCountdownCue(gender: VoiceGender = currentGender)", errors=errors, label="AIVoiceCalloutManager.kt")
    _assert_contains(android_voice_manager, "runtimeVoiceCueForElapsedMark", errors=errors, label="AIVoiceCalloutManager.kt")


def run_checks(repo_root: Path, *, include_voice: bool) -> list[str]:
    errors: list[str] = []
    check_android_retry_contract(repo_root, errors)
    check_native_release_contract(repo_root, errors)
    check_play_public_listing_contract(repo_root, errors)
    if include_voice:
        check_voice_contract(repo_root, errors)
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fast regression guardrails.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("staged", "ci"), default="staged")
    parser.add_argument("--paths", nargs="*", default=None, help="Optional explicit paths to evaluate instead of git staged files.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(args.repo_root).resolve()

    candidate_paths = _normalize_paths(args.paths) if args.paths is not None else _git_staged_paths(repo_root)
    matched_paths = relevant_paths(candidate_paths)
    include_voice = args.mode == "ci" or any(_matches_voice_path(path) for path in matched_paths)

    if args.mode == "staged" and not matched_paths:
        print("regression_guards: skip (no staged voice/store regression paths)")
        return 0

    errors = run_checks(repo_root, include_voice=include_voice)
    if errors:
        print("regression_guards: FAILED")
        for error in errors:
            print(f" - {error}")
        return 1

    if matched_paths:
        print("regression_guards: ok for")
        for path in matched_paths:
            print(f" - {path}")
    else:
        print("regression_guards: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
