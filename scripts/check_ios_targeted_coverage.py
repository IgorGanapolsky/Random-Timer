from __future__ import annotations

import argparse
import json
from pathlib import Path


def _iter_file_coverages(node: object):
    if isinstance(node, dict):
        path = node.get("path")
        line_coverage = node.get("lineCoverage")
        if isinstance(path, str) and isinstance(line_coverage, (int, float)):
            yield path, float(line_coverage)
        for key in ("targets", "files"):
            children = node.get(key)
            if isinstance(children, list):
                for child in children:
                    yield from _iter_file_coverages(child)
    elif isinstance(node, list):
        for child in node:
            yield from _iter_file_coverages(child)


def load_coverages(report_json: Path) -> dict[str, float]:
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    return {path: coverage for path, coverage in _iter_file_coverages(payload)}


def parse_requirement(raw: str) -> tuple[str, float]:
    suffix, sep, threshold = raw.rpartition("=")
    if not sep:
        raise argparse.ArgumentTypeError("coverage requirement must look like path/suffix.swift=1.0")
    return suffix, float(threshold)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail if targeted iOS source files are below the required line coverage.")
    parser.add_argument("--report-json", required=True, help="Path to xccov --json report")
    parser.add_argument(
        "--require",
        action="append",
        type=parse_requirement,
        default=[],
        help="Coverage requirement in the form path/suffix.swift=1.0",
    )
    args = parser.parse_args()

    coverages = load_coverages(Path(args.report_json))
    if not args.require:
        raise SystemExit("No --require entries provided.")

    failures: list[str] = []
    for suffix, threshold in args.require:
        matches = [(path, coverage) for path, coverage in coverages.items() if path.endswith(suffix)]
        if not matches:
            failures.append(f"missing coverage entry for suffix: {suffix}")
            continue
        if len(matches) > 1:
            failures.append(f"ambiguous coverage suffix {suffix}: {[path for path, _ in matches]}")
            continue
        path, coverage = matches[0]
        print(f"{path}: {coverage:.3%} (required {threshold:.1%})")
        if coverage + 1e-9 < threshold:
            failures.append(f"{path} covered at {coverage:.3%}, below required {threshold:.1%}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("iOS targeted coverage check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
