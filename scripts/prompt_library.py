from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_manifest_path() -> Path:
    return repo_root() / "marketing" / "data" / "prompt_library.json"


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    prompt_ids = [entry["id"] for entry in manifest["prompts"]]
    if len(prompt_ids) != len(set(prompt_ids)):
        raise ValueError("prompt_library.json contains duplicate prompt ids")
    return manifest


def _render_text(manifest: dict) -> str:
    lines = [f"Prompt library ({len(manifest['prompts'])} packs)"]
    for entry in manifest["prompts"]:
        lines.append(f"- {entry['id']}: {entry['title']} [{entry['primary_metric']}]")
        lines.append(f"  file: {entry['path']}")
    return "\n".join(lines) + "\n"


def _render_json(manifest: dict) -> str:
    payload = {
        "count": len(manifest["prompts"]),
        "prompts": manifest["prompts"],
    }
    return json.dumps(payload, indent=2) + "\n"


def _show_prompt(manifest: dict, prompt_id: str) -> str:
    for entry in manifest["prompts"]:
        if entry["id"] == prompt_id:
            prompt_path = repo_root() / entry["path"]
            return prompt_path.read_text(encoding="utf-8")
    raise SystemExit(f"unknown prompt id: {prompt_id}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Random Timer prompt library")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=default_manifest_path(),
        help="Path to prompt_library.json",
    )
    parser.add_argument("--list", action="store_true", help="List prompt packs")
    parser.add_argument(
        "--show",
        metavar="PROMPT_ID",
        help="Print the markdown body for a prompt pack",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for --list",
    )
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)

    if args.show:
        print(_show_prompt(manifest, args.show), end="")
        return 0

    if args.list:
        if args.format == "json":
            print(_render_json(manifest), end="")
        else:
            print(_render_text(manifest), end="")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
