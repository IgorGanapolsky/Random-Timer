from __future__ import annotations

import subprocess
from pathlib import Path


def test_ai_mobile_guardrails_ci_contract_passes() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "ai-mobile-guardrails.sh"
    assert script.exists(), "ai-mobile-guardrails.sh should exist"

    result = subprocess.run(
        ["bash", str(script), "--ci"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise AssertionError(
            "ai-mobile-guardrails failed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}\n"
        )


def test_ios_volume_slider_commits_changes_on_release() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (
        repo_root
        / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
    ).read_text(encoding="utf-8")
    volume_slider_block = source.split("private struct VolumeSliderView", 1)[1]

    assert "onEditingChanged:" in volume_slider_block
    slider_binding = volume_slider_block.split("Slider(", 1)[1].split("onEditingChanged:", 1)[0]
    assert "onChanged(next)" not in slider_binding
    assert volume_slider_block.count("onChanged(next)") == 3


def test_ui_ux_audit_handles_indented_kotlin_closing_braces() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "scripts/ui-ux-audit.sh").read_text(encoding="utf-8")

    assert "awk '/private fun VolumeSlider\\(/,/^\\s*}/'" in source
    assert "awk '/private fun NudgeButton\\(/,/^\\s*}/'" in source
