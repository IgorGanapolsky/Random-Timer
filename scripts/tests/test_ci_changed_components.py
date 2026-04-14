from __future__ import annotations

from scripts.ci_changed_components import classify


def test_workflow_only_changes_skip_native_heavy_jobs() -> None:
    result = classify(
        [
            ".github/workflows/ci.yml",
            ".github/workflows/device-tests.yml",
            "scripts/tests/test_workflow_security_contracts.py",
        ]
    )

    assert result == {
        "android": False,
        "ios": False,
        "android_device": False,
        "ios_device": False,
    }


def test_android_changes_enable_android_and_device_jobs_only() -> None:
    result = classify(["native-android/app/src/main/java/com/example/Timer.kt"])

    assert result == {
        "android": True,
        "ios": False,
        "android_device": True,
        "ios_device": False,
    }


def test_ios_changes_enable_ios_and_device_jobs_only() -> None:
    result = classify(["native-ios/RandomTimer/TimerSetupScreen.swift"])

    assert result == {
        "android": False,
        "ios": True,
        "android_device": False,
        "ios_device": True,
    }


def test_shared_app_assets_enable_both_platforms() -> None:
    result = classify(["content/pro_audio/monthly_pro_audio_packs.json"])

    assert result == {
        "android": True,
        "ios": True,
        "android_device": True,
        "ios_device": True,
    }


def test_non_pr_events_force_all_jobs() -> None:
    result = classify(["docs/README.md"], force_all=True)

    assert result == {
        "android": True,
        "ios": True,
        "android_device": True,
        "ios_device": True,
    }
