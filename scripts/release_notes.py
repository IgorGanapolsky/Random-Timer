#!/usr/bin/env python3
"""Helpers for versioned release notes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PLACEHOLDER_MARKERS = (
    "TODO:",
    "TBD",
    "REPLACE_THIS_PLACEHOLDER",
    "<fill",
)


class ReleaseNotesError(RuntimeError):
    """Raised when versioned release notes are missing or incomplete."""


def release_notes_path(repo_root: Path, version: str) -> Path:
    return repo_root / "release-notes" / f"{version}.md"


def is_placeholder_release_notes(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return True

    upper = normalized.upper()
    return any(marker in normalized for marker in PLACEHOLDER_MARKERS) or "TODO" in upper or "TBD" in upper


def read_and_validate_release_notes(repo_root: Path, version: str) -> tuple[Path, str]:
    path = release_notes_path(repo_root, version)
    if not path.is_file():
        raise ReleaseNotesError(
            f"Versioned release notes missing: expected {path.relative_to(repo_root)} for release {version}"
        )

    text = path.read_text(encoding="utf-8").strip()
    if is_placeholder_release_notes(text):
        raise ReleaseNotesError(
            f"Versioned release notes still contain placeholder content: {path.relative_to(repo_root)}"
        )

    return path, text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate or print versioned release notes.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--version", required=True, help="Semantic version, e.g. 1.3.18")
    parser.add_argument(
        "--print-body",
        action="store_true",
        help="Print the validated release note body to stdout instead of a status line.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()

    try:
        path, text = read_and_validate_release_notes(repo_root=repo_root, version=args.version)
    except ReleaseNotesError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.print_body:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return 0

    print(f"[OK] Release notes ready: {path.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
