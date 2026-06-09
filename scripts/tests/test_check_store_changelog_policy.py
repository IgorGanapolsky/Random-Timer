from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_store_changelog_policy import (
    ANDROID_CHANGELOG_DIR,
    IOS_RELEASE_NOTES,
    find_violations,
    main,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_store_changelogs_have_no_denylisted_terms() -> None:
    violations = find_violations()
    offending = [
        f"{v.path.relative_to(REPO_ROOT)}:{v.line_number} ({v.term})"
        for v in violations
    ]
    assert not offending, "Store changelog denylist violations:\n" + "\n".join(offending)


def test_main_returns_zero_when_policy_clean() -> None:
    assert main([]) == 0


def test_scan_detects_backdoor_in_temp_changelog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    changelog_dir = tmp_path / "changelogs"
    changelog_dir.mkdir()
    (changelog_dir / "99.txt").write_text("- Fixed backdoor gesture.\n", encoding="utf-8")

    monkeypatch.setattr(
        "scripts.check_store_changelog_policy.ANDROID_CHANGELOG_DIR",
        changelog_dir,
    )
    monkeypatch.setattr(
        "scripts.check_store_changelog_policy.IOS_RELEASE_NOTES",
        tmp_path / "missing_release_notes.txt",
    )
    monkeypatch.setattr(
        "scripts.check_store_changelog_policy.RELEASE_NOTES_DIR",
        tmp_path / "release-notes",
    )

    violations = find_violations()
    terms = {v.term for v in violations}
    assert "backdoor" in terms
    assert "gesture" in terms
    assert main([]) == 1
