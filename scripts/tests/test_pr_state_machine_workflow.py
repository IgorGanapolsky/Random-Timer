from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PR_STATE_MACHINE_WORKFLOW = ROOT / ".github/workflows/pr-state-machine.yml"


def test_pr_state_machine_reconciles_when_ci_workflow_completes():
    source = PR_STATE_MACHINE_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_run:" in source
    assert 'workflows: ["CI"]' in source
    assert "types: [completed]" in source
    assert 'context.eventName === "workflow_run"' in source
    assert "workflowRun.head_sha" in source
    assert "listPullRequestsAssociatedWithCommit" in source


def test_pr_state_machine_reads_manual_dispatch_input_from_event_payload():
    source = PR_STATE_MACHINE_WORKFLOW.read_text(encoding="utf-8")

    assert "context.payload.inputs?.pr_number ?? \"\"" in source
    assert 'core.getInput("pr_number")' not in source
