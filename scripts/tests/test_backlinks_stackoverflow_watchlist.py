"""Referral pipeline writes Stack Overflow watchlist for human use."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_run_referral_writes_stackoverflow_watchlist(tmp_path: Path) -> None:
    from scripts import backlinks_referral as br

    br.run_referral(tmp_path)
    md = tmp_path / "marketing" / "referral_content" / "stackoverflow_watchlist.md"
    assert md.is_file()
    text = md.read_text(encoding="utf-8")
    assert "stackoverflow.com/questions/tagged" in text
    assert "STACK_OVERFLOW_PLAYBOOK" in text
