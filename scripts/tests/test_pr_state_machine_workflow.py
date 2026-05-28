from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PR_STATE_MACHINE_WORKFLOW = ROOT / ".github/workflows/pr-state-machine.yml"


def test_pr_state_machine_reconciles_when_ci_workflow_completes():
    source = PR_STATE_MACHINE_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_run:" in source
    assert 'workflows: [CI, Device Tests]' in source
    assert "listPullRequestsAssociatedWithCommit" in source
    assert "workflow_dispatch:" in source or "workflow_dispatch" in source
    assert "check_suite:" not in source


def test_pr_state_machine_reads_manual_dispatch_input_from_event_payload():
    source = PR_STATE_MACHINE_WORKFLOW.read_text(encoding="utf-8")

    assert 'core.getInput("pr_number")' in source
    assert "pr_number:" in source


def test_pr_state_machine_does_not_emit_legacy_commit_status():
    source = PR_STATE_MACHINE_WORKFLOW.read_text(encoding="utf-8")

    assert "createCommitStatus" not in source
    assert 'context: "pr/state-machine"' not in source
