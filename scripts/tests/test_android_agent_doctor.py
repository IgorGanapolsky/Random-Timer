from pathlib import Path

from scripts.android_agent_doctor import build_report
from scripts.android_agent_doctor import main


def test_build_report_detects_android_repo_shape_and_versions(tmp_path: Path, monkeypatch) -> None:
    android_root = tmp_path / "native-android"
    app_root = android_root / "app/src/main"
    app_root.mkdir(parents=True)
    (android_root / "gradlew").write_text("#!/bin/sh\n", encoding="utf-8")
    (android_root / "app").mkdir(exist_ok=True)
    (android_root / "app/build.gradle.kts").write_text(
        """
android {
    compileSdk = 36
    defaultConfig {
        minSdk = 26
        targetSdk = 36
    }
}
""",
        encoding="utf-8",
    )
    (app_root / "AndroidManifest.xml").write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example.timer" />',
        encoding="utf-8",
    )
    monkeypatch.setenv("PATH", str(tmp_path))

    report = build_report(tmp_path)

    assert report["android_root_exists"] is True
    assert report["gradle_wrapper_exists"] is True
    assert report["manifest_exists"] is True
    assert report["package"] == "com.example.timer"
    assert report["gradle_versions"] == {"compileSdk": "36", "minSdk": "26", "targetSdk": "36"}
    assert report["tools"]["android_cli"]["available"] is False
    assert "Android CLI is not installed on PATH" in report["warnings"][0]


def test_main_json_output(capsys, tmp_path: Path) -> None:
    status = main(["--repo-root", str(tmp_path), "--json"])

    assert status == 0
    assert '"high_roi_recommendations"' in capsys.readouterr().out
