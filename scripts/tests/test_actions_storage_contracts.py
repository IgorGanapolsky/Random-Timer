from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


HIGH_VOLUME_WORKFLOWS = [
    ".github/workflows/ci.yml",
    ".github/workflows/device-tests.yml",
    ".github/workflows/internal-distribution.yml",
    ".github/workflows/native-release.yml",
    ".github/workflows/android17-canary.yml",
    ".github/workflows/daily-growth-publishing.yml",
    ".github/workflows/store-console-verification.yml",
]


def _upload_artifact_blocks(text: str) -> list[str]:
    marker = "uses: actions/upload-artifact@"
    blocks: list[str] = []
    parts = text.split(marker)
    for part in parts[1:]:
        next_step = part.find("\n      - name:")
        blocks.append(part if next_step == -1 else part[:next_step])
    return blocks


def test_high_volume_upload_artifacts_use_short_retention() -> None:
    offenders: list[str] = []
    for workflow in HIGH_VOLUME_WORKFLOWS:
        text = (ROOT / workflow).read_text(encoding="utf-8")
        for block in _upload_artifact_blocks(text):
            if "retention-days: 1" not in block:
                offenders.append(workflow)
                break

    assert offenders == []


def test_device_tests_do_not_cache_android_emulator_images() -> None:
    text = (ROOT / ".github/workflows/device-tests.yml").read_text(encoding="utf-8")

    assert "avd-api-30" not in text
    assert "~/.android/avd" not in text


def test_high_volume_workflows_do_not_use_gradle_actions_cache() -> None:
    offenders = []
    for workflow in HIGH_VOLUME_WORKFLOWS:
        text = (ROOT / workflow).read_text(encoding="utf-8")
        if "cache: 'gradle'" in text or "cache: gradle" in text:
            offenders.append(workflow)

    assert offenders == []
