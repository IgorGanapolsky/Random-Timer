#!/usr/bin/env python3
"""Stub triage script: Google Play project is currently deleted."""
import json
import sys


def is_failed_precondition_payload(payload: dict) -> bool:
    response = payload.get("response", "")
    return "FAILED_PRECONDITION" in response


def should_close_issue(result: dict) -> bool:
    return (
        result.get("requested_track") == "production"
        and result.get("effective_track") == "production"
        and not result.get("fallback_used", True)
        and not result.get("precondition_blocked", True)
    )


def build_issue_body(run_url: str, error_payload: dict, result_payload: dict) -> str:
    return (
        f"## Play Precondition Triage\n\n"
        f"**Run:** {run_url}\n\n"
        f"### Error\n```json\n{json.dumps(error_payload, indent=2)}\n```\n\n"
        f"### Result\n```json\n{json.dumps(result_payload, indent=2)}\n```\n"
    )


if __name__ == "__main__":
    print("Stub triage script: Google Play project is currently deleted.")
    sys.exit(0)
