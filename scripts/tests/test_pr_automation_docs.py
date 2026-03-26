from pathlib import Path


README = Path("README.md")
BUGBOT = Path("BUGBOT.md")


def test_readme_documents_pr_automation_stack() -> None:
    content = README.read_text(encoding="utf-8")

    assert "## PR Automation Stack" in content
    assert "Seer by Sentry" in content
    assert "Claude Review" in content
    assert "GitHub Copilot code review" in content
    assert "SonarQube Cloud" in content
    assert "Cursor BugBot / `@cursor` agent" in content
    assert "BUGBOT.md" in content


def test_bugbot_contract_exists_and_mentions_cursor_review_scope() -> None:
    content = BUGBOT.read_text(encoding="utf-8")

    assert "Cursor BugBot" in content
    assert "bug-first mindset" in content
    assert "store, billing, timer, alarm, audio, CI, and secret-handling" in content
