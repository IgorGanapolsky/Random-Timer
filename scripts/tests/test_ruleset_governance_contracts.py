from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILE = ROOT / ".github/settings.yml"


def test_repo_settings_do_not_manage_classic_branch_protection():
    settings = SETTINGS_FILE.read_text(encoding="utf-8")

    assert "\nbranches:\n" not in settings


def test_classic_branch_protection_sync_files_are_removed():
    assert not (ROOT / ".github/branch-protection.yml").exists()
    assert not (ROOT / ".github/workflows/branch-protection-sync.yml").exists()
    assert not (ROOT / ".github/scripts/setup-branch-protection.sh").exists()
