#!/usr/bin/env python3
"""Fail if public store changelog copy contains internal/security denylist terms."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ANDROID_CHANGELOG_DIR = (
    REPO_ROOT / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "changelogs"
)
IOS_RELEASE_NOTES = REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "release_notes.txt"
RELEASE_NOTES_DIR = REPO_ROOT / "release-notes"

# High-risk terms that must never appear in Play/App Store "What's New" copy.
STORE_DENYLIST = (
    "backdoor",
    "secret",
    "debug",
    "test-only",
    "gesture",
    "bypass",
    "cheat",
)

# Substrings that are allowed even when a denylist term matches (product/marketing copy).
ALLOWLIST_SUBSTRINGS = (
    "hidden countdown",
    "stealth countdown",
)

_DENYLIST_PATTERNS = {
    term: re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    for term in STORE_DENYLIST
}


@dataclass(frozen=True)
class Violation:
    path: Path
    term: str
    line_number: int
    line_text: str


def _is_allowlisted(line: str, term: str) -> bool:
    lowered = line.lower()
    if term.lower() == "hidden":
        return any(fragment in lowered for fragment in ALLOWLIST_SUBSTRINGS)
    return False


def _scan_file(path: Path, denylist: tuple[str, ...]) -> list[Violation]:
    violations: list[Violation] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return violations

    for line_number, line in enumerate(text.splitlines(), start=1):
        for term in denylist:
            if not _DENYLIST_PATTERNS[term].search(line):
                continue
            if _is_allowlisted(line, term):
                continue
            violations.append(
                Violation(
                    path=path,
                    term=term,
                    line_number=line_number,
                    line_text=line.strip(),
                )
            )
    return violations


def collect_store_changelog_paths() -> list[Path]:
    paths: list[Path] = []
    if ANDROID_CHANGELOG_DIR.is_dir():
        paths.extend(sorted(ANDROID_CHANGELOG_DIR.glob("*.txt")))
    if IOS_RELEASE_NOTES.is_file():
        paths.append(IOS_RELEASE_NOTES)
    return paths


def collect_release_note_paths() -> list[Path]:
    if not RELEASE_NOTES_DIR.is_dir():
        return []
    return sorted(RELEASE_NOTES_DIR.glob("*.md"))


def find_violations() -> list[Violation]:
    violations: list[Violation] = []
    for path in collect_store_changelog_paths():
        violations.extend(_scan_file(path, STORE_DENYLIST))
    for path in collect_release_note_paths():
        violations.extend(_scan_file(path, STORE_DENYLIST))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check store changelog policy.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print violations as JSON lines (path, term, line).",
    )
    args = parser.parse_args(argv)

    violations = find_violations()
    if not violations:
        print("✅ Store changelog policy check passed.")
        return 0

    for violation in violations:
        try:
            rel = violation.path.relative_to(REPO_ROOT)
        except ValueError:
            rel = violation.path
        if args.json:
            print(
                f'{{"path":"{rel}","term":"{violation.term}","line":{violation.line_number}}}'
            )
        else:
            print(
                f"❌ {rel}:{violation.line_number} contains denylisted term "
                f"'{violation.term}': {violation.line_text}"
            )

    print(f"Found {len(violations)} store changelog policy violation(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
