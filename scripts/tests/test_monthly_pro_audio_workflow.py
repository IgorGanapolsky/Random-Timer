from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "generate-ios-voice-callouts.yml"
LEGACY_WORKFLOW = ROOT / ".github" / "workflows" / "monthly-audio-pack.yml"


def test_monthly_audio_workflow_is_authoritative_and_fail_fast() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert LEGACY_WORKFLOW.exists() is False
    assert "0 6 1 * *" in source
    assert "roll_monthly_pro_audio_pack.py" in source
    assert 'pack_id="$(python scripts/roll_monthly_pro_audio_pack.py' in source
    assert 'json.load(sys.stdin)["activePackId"]' in source
    assert "pro_audio_freshness.py" in source
    assert "gh pr merge --auto --squash" in source
    assert "|| true" not in source
