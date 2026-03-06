from __future__ import annotations

import subprocess
from pathlib import Path


def test_ai_mobile_guardrails_ci_contract_passes() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "ai-mobile-guardrails.sh"
    assert script.exists(), "ai-mobile-guardrails.sh should exist"

    result = subprocess.run(
        ["bash", str(script), "--ci"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise AssertionError(
            "ai-mobile-guardrails failed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}\n"
        )

