"""Compaction-safe artifact vault + tool-trace transparency.

From Simon Willison (2026-09-12): GPT-6 Astra / ChatGPT Work produced GPX,
GeoJSON, and a shareable map HTML — but the UI hid the code and compaction
later made the Python unrecoverable. That opacity is an anti-feature.

Source: https://simonwillison.net/2026/Sep/12/astra-running-routes/

Policy for this fleet:
1. Persist tool traces, generated code, and downloadable artifacts before
   any session compaction.
2. Expose pre-compaction text via an explicit recall tool/API.
3. Prefer fetch-open-data + local compute over opaque chat narratives.
4. Share visualizations as HTML with embedded JSON and allowlisted CDNs only.

Fleet cap: FLEET_MONTHLY_CAP_USD ($20).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

FLEET_MONTHLY_CAP_USD = 20.0

ALLOWED_PLATFORMS = frozenset(
    {
        "artifact_transparency",
        "agent_artifact_transparency",
        "compaction_safe_vault",
        "astra_transparency",
    }
)
OPAQUE_MARKERS = (
    "opaque_chat_only",
    "chat_only_agent",
    "hide_tool_trace",
    "no_artifact_persistence",
)

ALLOWED_CDN_HOSTS = frozenset(
    {
        "cdnjs.cloudflare.com",
        "esm.sh",
        "cdn.jsdelivr.net",
        "unpkg.com",
        "fonts.googleapis.com",
        "fonts.gstatic.com",
        "fonts.bunny.net",
    }
)


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str
    score: float = 0.0


def _norm(value: str) -> str:
    return (
        (value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(".", "_")
        .replace(" ", "_")
    )


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_artifact_transparency",
            ok=True,
            reason="compaction-safe artifact vault under fleet cap",
        )
    if any(marker in name for marker in OPAQUE_MARKERS):
        return ControlDecision(
            action="block_opaque_chat_only",
            ok=False,
            reason="reject chat-only opacity; persist recoverable artifacts",
        )
    return ControlDecision(
        action="block_unknown_platform",
        ok=False,
        reason="unknown artifact-transparency platform denied",
    )


def evaluate_transparency(
    *,
    tool_trace_present: bool,
    generated_code_persisted: bool,
    downloadable_artifacts: Sequence[str],
    narrative_only_explanation: bool,
) -> ControlDecision:
    artifacts = [a for a in downloadable_artifacts if str(a).strip()]
    if not tool_trace_present:
        return ControlDecision(
            action="block_missing_tool_trace",
            ok=False,
            reason="tool trace required (e.g. Nominatim/Overpass/local_compute)",
        )
    if not generated_code_persisted:
        return ControlDecision(
            action="block_unrecoverable_code",
            ok=False,
            reason="generated code must be persisted before compaction",
        )
    if not artifacts:
        return ControlDecision(
            action="block_chat_only_deliverable",
            ok=False,
            reason="require downloadable artifacts (geojson/gpx/html/json)",
        )
    if narrative_only_explanation and not generated_code_persisted:
        return ControlDecision(
            action="block_narrative_without_code",
            ok=False,
            reason="narrative explanations are not a substitute for code",
        )
    return ControlDecision(
        action="allow_transparent_artifacts",
        ok=True,
        reason="tool trace, code, and downloadable artifacts are recoverable",
        score=float(len(artifacts)),
    )


def _run_dir(vault_root: Path, run_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in run_id.strip())
    if not safe:
        raise ValueError("run_id required")
    return vault_root / safe


def persist_run_artifacts(
    *,
    vault_root: Path,
    run_id: str,
    tool_trace: Sequence[Mapping[str, Any]],
    generated_code: str,
    artifacts: Mapping[str, str],
    pre_compaction_text: str,
) -> dict[str, Any]:
    gate = evaluate_transparency(
        tool_trace_present=bool(tool_trace),
        generated_code_persisted=bool(generated_code.strip()),
        downloadable_artifacts=tuple(artifacts.keys()),
        narrative_only_explanation=False,
    )
    if not gate.ok:
        return {"ok": False, "action": gate.action, "reason": gate.reason}

    root = _run_dir(vault_root, run_id)
    root.mkdir(parents=True, exist_ok=True)
    (root / "tool_trace.json").write_text(
        json.dumps(list(tool_trace), indent=2) + "\n", encoding="utf-8"
    )
    (root / "generated_code.py").write_text(generated_code, encoding="utf-8")
    (root / "pre_compaction.txt").write_text(pre_compaction_text, encoding="utf-8")
    artifact_dir = root / "artifacts"
    artifact_dir.mkdir(exist_ok=True)
    written: list[str] = []
    for name, content in artifacts.items():
        safe_name = Path(name).name
        path = artifact_dir / safe_name
        path.write_text(content, encoding="utf-8")
        # Convenience alias at run root for common deliverables.
        (root / safe_name).write_text(content, encoding="utf-8")
        written.append(safe_name)

    meta = {
        "run_id": run_id,
        "compacted": False,
        "artifact_names": written,
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "posture": "fetch_open_data_then_local_compute",
    }
    (root / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "action": "persisted", "path": str(root), "artifacts": written}


def compact_session(*, vault_root: Path, run_id: str) -> dict[str, Any]:
    """Mark a run compacted without deleting pre-compaction vault contents."""
    root = _run_dir(vault_root, run_id)
    meta_path = root / "meta.json"
    if not meta_path.exists():
        return {
            "ok": False,
            "action": "block_missing_vault_run",
            "reason": f"no vault run for {run_id}",
        }
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["compacted"] = True
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    # Live session transcript may be dropped; vault retains recoverable files.
    live = root / "live_session.txt"
    if live.exists():
        live.unlink()
    return {"ok": True, "action": "compacted", "path": str(root)}


def recall_pre_compaction(*, vault_root: Path, run_id: str) -> dict[str, Any]:
    root = _run_dir(vault_root, run_id)
    if not (root / "meta.json").exists():
        return {
            "ok": False,
            "action": "block_missing_vault_run",
            "reason": f"no vault run for {run_id}",
        }
    return {
        "ok": True,
        "action": "recalled",
        "run_id": run_id,
        "pre_compaction_text": (root / "pre_compaction.txt").read_text(encoding="utf-8"),
        "generated_code": (root / "generated_code.py").read_text(encoding="utf-8"),
        "tool_trace": json.loads((root / "tool_trace.json").read_text(encoding="utf-8")),
        "meta": json.loads((root / "meta.json").read_text(encoding="utf-8")),
        "path": str(root),
    }


def validate_cdn_url(*, url: str) -> ControlDecision:
    host = (urlparse(url).hostname or "").lower()
    if host in ALLOWED_CDN_HOSTS:
        return ControlDecision(
            action="allow_cdn",
            ok=True,
            reason=f"CDN host allowlisted: {host}",
        )
    return ControlDecision(
        action="block_cdn_not_allowlisted",
        ok=False,
        reason=f"CDN host not allowlisted: {host or 'missing'}",
    )


def render_share_html(
    *,
    title: str,
    subtitle: str,
    data: Mapping[str, Any],
    attribution: str,
    cdn_script: str = "https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js",
) -> str:
    cdn = validate_cdn_url(url=cdn_script)
    if not cdn.ok:
        raise ValueError(cdn.reason)
    payload = json.dumps(data, separators=(",", ":"))
    # Keep markup close to the Willison/Astra visualize skill pattern.
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{_escape(title)}</title>
</head>
<body>
<div id="eg-share-loop">
  <div class="viz-row"><h3>{_escape(title)}</h3><span class="text-small">{_escape(subtitle)}</span></div>
  <div id="eg-share-stage"></div>
  <div class="text-small text-muted">{_escape(attribution)}</div>
  <style>
    #eg-share-loop {{ width:100%; }}
    #eg-share-loop #eg-share-stage {{ width:100%; margin:8px 0; min-height:120px; }}
    #eg-share-loop .eg-share-map {{ display:block; width:100%; }}
  </style>
  <script type="application/json" id="eg-share-data">{payload}</script>
  <script src="{_escape(cdn_script)}"></script>
  <script>
  (() => {{
    const root = document.getElementById('eg-share-loop');
    const stage = document.getElementById('eg-share-stage');
    const raw = document.getElementById('eg-share-data').textContent;
    const data = JSON.parse(raw);
    stage.textContent = 'embedded data keys: ' + Object.keys(data).join(', ');
  }})();
  </script>
</div>
</body>
</html>
"""


def _escape(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def doctor() -> dict[str, Any]:
    return {
        "ok": True,
        "module": "scripts/agent_artifact_transparency.py",
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "source": "https://simonwillison.net/2026/Sep/12/astra-running-routes/",
        "posture": [
            "persist_tool_trace",
            "persist_generated_code",
            "persist_downloadable_artifacts",
            "recall_pre_compaction_via_tool",
            "allowlisted_cdn_visualize_html",
            "fetch_open_data_then_local_compute",
        ],
        "allowed_cdn_hosts": sorted(ALLOWED_CDN_HOSTS),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compaction-safe artifact vault and share HTML renderer"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")

    p_persist = sub.add_parser("persist", help="Persist a run into the vault")
    p_persist.add_argument("--vault", type=Path, required=True)
    p_persist.add_argument("--run-id", required=True)
    p_persist.add_argument("--code", type=Path, required=True)
    p_persist.add_argument("--trace-json", type=Path, required=True)
    p_persist.add_argument("--pre-text", type=Path, required=True)
    p_persist.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="name=path pairs for downloadable artifacts",
    )

    p_recall = sub.add_parser("recall", help="Recall pre-compaction artifacts")
    p_recall.add_argument("--vault", type=Path, required=True)
    p_recall.add_argument("--run-id", required=True)

    p_html = sub.add_parser("share-html", help="Render allowlisted share HTML")
    p_html.add_argument("--title", required=True)
    p_html.add_argument("--subtitle", default="")
    p_html.add_argument("--data-json", type=Path, required=True)
    p_html.add_argument("--attribution", default="Map data © OpenStreetMap contributors")
    p_html.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "doctor":
        print(json.dumps(doctor(), indent=2))
        return 0

    if args.cmd == "persist":
        artifacts: dict[str, str] = {}
        for item in args.artifact:
            if "=" not in item:
                parser.error(f"artifact must be name=path, got {item}")
            name, path_s = item.split("=", 1)
            artifacts[name] = Path(path_s).read_text(encoding="utf-8")
        result = persist_run_artifacts(
            vault_root=args.vault,
            run_id=args.run_id,
            tool_trace=json.loads(args.trace_json.read_text(encoding="utf-8")),
            generated_code=args.code.read_text(encoding="utf-8"),
            artifacts=artifacts,
            pre_compaction_text=args.pre_text.read_text(encoding="utf-8"),
        )
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.cmd == "recall":
        result = recall_pre_compaction(vault_root=args.vault, run_id=args.run_id)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.cmd == "share-html":
        data = json.loads(args.data_json.read_text(encoding="utf-8"))
        html = render_share_html(
            title=args.title,
            subtitle=args.subtitle,
            data=data,
            attribution=args.attribution,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(html, encoding="utf-8")
        print(json.dumps({"ok": True, "path": str(args.out)}, indent=2))
        return 0

    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
