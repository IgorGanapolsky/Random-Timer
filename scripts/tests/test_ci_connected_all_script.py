from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/device-tests/ci-connected-all.sh"


def test_ci_connected_all_runs_full_connected_debug_android_test_suite():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "./gradlew connectedDebugAndroidTest" in source
    assert "testInstrumentationRunnerArguments.class" in source
    assert "am force-stop com.iganapolsky.randomtimer" in source
    assert "NotificationE2ETest" in source
    assert "-PenableFirebasePlugins=false" in source
    assert source.count('for test_class in ${TEST_CLASSES}') == 1
    assert source.count("com.iganapolsky.randomtimer.") == 6


def test_ci_connected_all_lists_six_instrumentation_classes():
    source = SCRIPT.read_text(encoding="utf-8")
    for class_name in (
        "RangeSliderUiTest",
        "ActiveTimerScreenLandscapeLayoutTest",
        "ActiveTimerScreenTapCircleTest",
        "TimerSetupSmokeTest",
        "TimerForegroundServiceResetTest",
        "NotificationE2ETest",
    ):
        assert class_name in source


def test_ci_connected_all_is_referenced_by_native_release_workflow():
    workflow = (ROOT / ".github/workflows/native-release.yml").read_text(encoding="utf-8")

    assert "android-device-test-gate:" in workflow
    assert "scripts/device-tests/ci-connected-all.sh" in workflow
    assert "needs.android-device-test-gate.result == 'success'" in workflow
