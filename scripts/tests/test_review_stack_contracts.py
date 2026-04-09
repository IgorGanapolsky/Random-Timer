from pathlib import Path


README = Path("README.md")
PR_BOTS_DOC = Path("docs/pr-review-bots.md")
BUGBOT = Path("BUGBOT.md")
CURSOR_BUGBOT = Path(".cursor/BUGBOT.md")
CI_WORKFLOW = Path(".github/workflows/ci.yml")
CLAUDE_REVIEW_WORKFLOW = Path(".github/workflows/claude-review.yml")
SEER_APP = Path(".github/seer.app.yml")
COPILOT_INSTRUCTIONS = Path(".github/copilot-instructions.md")
SONAR_CONFIG = Path("config/sonar-project.properties")
CI_CONFIG = Path(".github/ci-config.yml")


def test_readme_surfaces_review_stack_badges() -> None:
    content = README.read_text(encoding="utf-8")

    assert "Claude Review" in content
    assert "GitHub Copilot Review" in content
    assert "Sentry Seer" in content
    assert "Cursor BugBot" in content
    assert "SonarQube Cloud" in content


def test_review_stack_docs_capture_enforcement_model() -> None:
    content = PR_BOTS_DOC.read_text(encoding="utf-8")

    assert "Claude Review" in content
    assert "GitHub Copilot code review" in content
    assert "Seer (Sentry)" in content
    assert "SonarQube Cloud" in content
    assert "Cursor BugBot" in content
    assert "not a live GitHub status check" in content


def test_review_stack_files_exist() -> None:
    assert CLAUDE_REVIEW_WORKFLOW.exists()
    assert SEER_APP.exists()
    assert COPILOT_INSTRUCTIONS.exists()
    assert BUGBOT.exists()
    assert CURSOR_BUGBOT.exists()
    assert SONAR_CONFIG.exists()


def test_ci_ai_review_gate_covers_copilot_and_sentry_threads() -> None:
    content = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "Enforce AI review thread resolution" in content
    assert '"sentry"' in content
    assert '"copilot-pull-request-reviewer[bot]"' in content


def test_ci_config_documents_tighter_review_requirements() -> None:
    content = CI_CONFIG.read_text(encoding="utf-8")

    assert "Claude Review" in content
    assert "Seer Code Review" in content
    assert "SonarCloud Code Analysis" in content
    assert "Android Emulator + Maestro Tests" in content
    assert "iOS Simulator + Maestro + Agent Device" in content
