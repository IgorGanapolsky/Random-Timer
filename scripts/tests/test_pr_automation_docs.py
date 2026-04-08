from pathlib import Path


README = Path("README.md")
PR_BOTS_DOC = Path("docs/pr-review-bots.md")
BUGBOT = Path("BUGBOT.md")


def test_readme_links_pr_review_bots_doc() -> None:
    readme = README.read_text(encoding="utf-8")
    assert "docs/pr-review-bots.md" in readme


def test_pr_review_bots_doc_documents_stack() -> None:
    content = PR_BOTS_DOC.read_text(encoding="utf-8")

    assert "Seer" in content
    assert "Claude Review" in content
    assert "Copilot" in content
    assert "SonarQube Cloud" in content
    assert "Cursor" in content
    assert "BUGBOT.md" in content


def test_bugbot_contract_exists_and_mentions_cursor_review_scope() -> None:
    content = BUGBOT.read_text(encoding="utf-8")

    assert "Cursor BugBot" in content
    assert "bug-first mindset" in content
    assert "store, billing, timer, alarm, audio, CI, and secret-handling" in content
