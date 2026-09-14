"""Tests for Compound Engineering lite gate."""

from __future__ import annotations

from pathlib import Path

from scripts import compound_gate as gate

COMPLETE = """---
title: "Fixture compound writeup"
date: "2026-09-14"
category: "process"
tags: ["compound-lite", "gate"]
status: active
source_pr: "fixture"
---

# Fixture compound writeup

## Problem

Agents finished PRs without writing durable learnings, so the same correction recurred.

## What worked

Added docs/solutions/ writeups plus scripts/compound_gate.py that rejects placeholders.

## Prevention

Run python3 scripts/compound_gate.py --json --slug <topic> after non-trivial merges.

## Evidence

- Command: pytest scripts/tests/test_compound_gate.py -q
- Merge SHA or CI URL (when shipped): fixture-local
"""


def test_assess_rejects_placeholders(tmp_path: Path) -> None:
    path = tmp_path / "x.md"
    path.write_text(
        "---\ntitle: t\ndate: YYYY-MM-DD\n---\n\n## Problem\n[short problem name]\n",
        encoding="utf-8",
    )
    result = gate.assess_solution(path)
    assert result["ok"] is False
    assert result["placeholder_hits"]


def test_evaluate_ready_with_solution(tmp_path: Path) -> None:
    (tmp_path / "templates" / "compound").mkdir(parents=True)
    (tmp_path / "templates" / "compound" / "SOLUTION.md").write_text("# t\n", encoding="utf-8")
    sol = tmp_path / "docs" / "solutions"
    sol.mkdir(parents=True)
    (sol / "003-compound-lite-fixture.md").write_text(COMPLETE, encoding="utf-8")
    report = gate.evaluate(tmp_path, slug="003")
    assert report["ready"] is True
    assert report["solution_count"] == 1


def test_evaluate_requires_solutions_by_default(tmp_path: Path) -> None:
    (tmp_path / "templates" / "compound").mkdir(parents=True)
    (tmp_path / "templates" / "compound" / "SOLUTION.md").write_text("# t\n", encoding="utf-8")
    blocked = gate.evaluate(tmp_path)
    assert blocked["ready"] is False
    assert "missing_docs/solutions/*.md" in blocked["blockers"]
