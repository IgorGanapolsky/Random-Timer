from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github/workflows"


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def test_workflow_run_blocks_do_not_dedent_inside_literal_body() -> None:
    failures: list[str] = []

    for path in sorted(WORKFLOWS.glob("*.yml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if line.strip() not in {"run: |", "run: >"}:
                continue

            parent_indent = _indent(line)
            body_indent: int | None = None
            for body_index, body_line in enumerate(lines[index + 1 :], start=index + 2):
                if not body_line.strip():
                    continue

                current_indent = _indent(body_line)
                if current_indent <= parent_indent:
                    break

                if body_indent is None:
                    body_indent = current_indent
                elif current_indent < body_indent:
                    failures.append(
                        f"{path.relative_to(ROOT)}:{body_index} dedents inside run block "
                        f"started at line {index + 1}"
                    )

    assert failures == []
