from __future__ import annotations

import json
from pathlib import Path

from scripts import prompt_library as prompts


REQUIRED_IDS = {
    "ad_creative_briefs",
    "app_store_screenshot_prompts",
    "aso_copy",
    "incident_summary_prompts",
    "release_notes_and_review_response_prompts",
}

REQUIRED_SECTIONS = (
    "## Purpose",
    "## When To Use",
    "## Inputs",
    "## Prompt",
    "## Guardrails",
    "## Output",
)


def test_manifest_contains_expected_prompt_ids():
    manifest = prompts.load_manifest(prompts.default_manifest_path())
    assert {entry["id"] for entry in manifest["prompts"]} == REQUIRED_IDS


def test_prompt_files_exist_and_contain_required_sections():
    manifest = prompts.load_manifest(prompts.default_manifest_path())

    for entry in manifest["prompts"]:
        prompt_path = prompts.repo_root() / entry["path"]
        assert prompt_path.is_file(), f"missing prompt file: {entry['path']}"

        text = prompt_path.read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            assert section in text, f"{entry['id']} missing section {section}"


def test_list_prompts_json_returns_machine_readable_manifest(capsys):
    exit_code = prompts.main(["--list", "--format", "json"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == len(REQUIRED_IDS)
    assert {entry["id"] for entry in payload["prompts"]} == REQUIRED_IDS


def test_repo_readme_links_to_prompt_library():
    readme = (prompts.repo_root() / "README.md").read_text(encoding="utf-8")
    assert "docs/prompt-library/README.md" in readme
