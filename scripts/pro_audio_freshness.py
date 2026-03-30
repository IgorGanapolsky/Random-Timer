from __future__ import annotations

import argparse
import json
from datetime import UTC, date, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "content" / "pro_audio" / "monthly_pro_audio_packs.json"


def _month_key(day: date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def _previous_month(day: date) -> str:
    year = day.year
    month = day.month - 1
    if month == 0:
        year -= 1
        month = 12
    return f"{year:04d}-{month:02d}"


def allowed_release_months(today: date, grace_day_limit: int = 1) -> tuple[str, ...]:
    current = _month_key(today)
    if today.day <= grace_day_limit:
        return (_previous_month(today), current)
    return (current,)


def load_active_pack(manifest_path: Path) -> tuple[dict, dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    active_pack_id = manifest["activePackId"]
    pack = next((item for item in manifest["packs"] if item["id"] == active_pack_id), None)
    if pack is None:
        raise SystemExit(f"Active Pro audio pack '{active_pack_id}' is missing from {manifest_path}.")
    return manifest, pack


def verify_manifest_freshness(
    manifest_path: Path,
    *,
    today: date | None = None,
    grace_day_limit: int = 1,
) -> dict[str, object]:
    if today is None:
        today = datetime.now(UTC).date()

    manifest, pack = load_active_pack(manifest_path)
    allowed = allowed_release_months(today, grace_day_limit=grace_day_limit)
    release_month = pack["releaseMonth"]

    if release_month not in allowed:
        raise SystemExit(
            "Active Pro audio pack is stale: "
            f"activePackId={manifest['activePackId']} "
            f"releaseMonth={release_month} "
            f"allowed={list(allowed)} "
            f"checkedOn={today.isoformat()}"
        )

    return {
        "active_pack_id": manifest["activePackId"],
        "release_month": release_month,
        "checked_on": today.isoformat(),
        "allowed_release_months": allowed,
        "grace_day_limit": grace_day_limit,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the active Pro audio pack is fresh enough for the monthly content promise.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to the canonical monthly Pro audio manifest.",
    )
    parser.add_argument(
        "--today",
        type=str,
        default="",
        help="Optional YYYY-MM-DD override for deterministic checks.",
    )
    parser.add_argument(
        "--grace-day-limit",
        type=int,
        default=1,
        help="Allow the previous month's pack through this UTC day of the month.",
    )
    args = parser.parse_args()

    today = date.fromisoformat(args.today) if args.today else None
    evidence = verify_manifest_freshness(
        args.manifest,
        today=today,
        grace_day_limit=args.grace_day_limit,
    )
    print(
        json.dumps(
            {
                "status": "fresh",
                "activePackId": evidence["active_pack_id"],
                "releaseMonth": evidence["release_month"],
                "checkedOn": evidence["checked_on"],
                "allowedReleaseMonths": list(evidence["allowed_release_months"]),
                "graceDayLimit": evidence["grace_day_limit"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
