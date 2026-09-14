"""OpenAI-hosted sandbox environment policy for the agent fleet.

Docs: https://developers.openai.com/api/docs/guides/agents-api/environments/openai-hosted

High-ROI rules we adopt (without requiring paid hosted usage by default):
1. Prefer local workspace; escalate to openai_hosted only when isolated Linux
   compute is needed and fleet budget allows.
2. Default network access to disabled; restricted domains must be exact hosts.
3. Never inject OPENAI_API_KEY / PATH / CODEX_* into the sandbox env.
4. Wait for environment status connected before live file ops.
5. Nonzero setup_commands exit blocks agent start.
6. Publish /workspace/outputs into the compaction-safe artifact vault.
7. Templates cannot broaden network policy.
8. Delete sessions when done; treat container spend as fleet-cap constrained.

Fleet cap: FLEET_MONTHLY_CAP_USD ($20).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.agent_artifact_transparency import persist_run_artifacts

FLEET_MONTHLY_CAP_USD = 20.0
WORKSPACE_ROOT = "/workspace"
WORKSPACE_OUTPUTS = "/workspace/outputs"

ALLOWED_PLATFORMS = frozenset(
    {
        "openai_hosted",
        "agent_openai_hosted_env",
        "openai_hosted_sandbox",
        "hosted_agents_environment",
    }
)
UNMANAGED_MARKERS = (
    "unmanaged_raw_container",
    "always_enabled_network",
    "host_docker_socket",
    "inject_api_key_into_sandbox",
)

NETWORK_ACCESS = frozenset({"enabled", "disabled", "restricted"})
RESERVED_ENV_EXACT = frozenset({"PATH", "OPENAI_API_KEY"})
RESERVED_ENV_PREFIXES = ("CODEX_",)
_HOST_RE = re.compile(r"^[A-Za-z0-9.-]+$")


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
            action="allow_openai_hosted",
            ok=True,
            reason="openai_hosted sandbox policy under fleet cap",
        )
    if any(marker in name for marker in UNMANAGED_MARKERS):
        return ControlDecision(
            action="block_unmanaged_sandbox",
            ok=False,
            reason="reject unmanaged/raw container posture",
        )
    return ControlDecision(
        action="block_unknown_platform",
        ok=False,
        reason="unknown hosted-environment platform denied",
    )


def evaluate_restricted_domains(*, domains: Sequence[str]) -> ControlDecision:
    if not domains:
        return ControlDecision(
            action="block_restricted_empty",
            ok=False,
            reason="restricted mode requires 1–100 exact host names",
        )
    if len(domains) > 100:
        return ControlDecision(
            action="block_restricted_too_many",
            ok=False,
            reason="restricted mode allows at most 100 hosts",
        )
    bad: list[str] = []
    for host in domains:
        h = (host or "").strip()
        if (
            not h
            or "/" in h
            or ":" in h
            or "*" in h
            or h.startswith("http://")
            or h.startswith("https://")
            or not _HOST_RE.match(h)
            or h.startswith(".")
            or h.endswith(".")
        ):
            bad.append(host)
    if bad:
        return ControlDecision(
            action="block_restricted_invalid_hosts",
            ok=False,
            reason=(
                "restricted hosts must be exact hostnames "
                f"(no protocol/path/port/wildcard): {bad}"
            ),
        )
    return ControlDecision(
        action="allow_restricted_domains",
        ok=True,
        reason=f"{len(domains)} exact hosts allowlisted",
        score=float(len(domains)),
    )


def evaluate_network_policy(
    *,
    access: str,
    allowed_domains: Sequence[str] | None = None,
) -> ControlDecision:
    mode = (access or "").strip().lower()
    if mode not in NETWORK_ACCESS:
        return ControlDecision(
            action="block_unknown_network_access",
            ok=False,
            reason=f"network.access must be one of {sorted(NETWORK_ACCESS)}",
        )
    if mode == "disabled":
        return ControlDecision(
            action="allow_network_disabled",
            ok=True,
            reason="outbound network disabled (default safe/cheap posture)",
        )
    if mode == "enabled":
        return ControlDecision(
            action="allow_network_enabled",
            ok=True,
            reason="outbound network enabled; use only when required",
            score=1.0,
        )
    domains = list(allowed_domains or [])
    return evaluate_restricted_domains(domains=domains)


def evaluate_reserved_env(*, env: Mapping[str, str]) -> ControlDecision:
    rejected: list[str] = []
    for key in env:
        k = str(key)
        if k in RESERVED_ENV_EXACT or k.startswith(RESERVED_ENV_PREFIXES):
            rejected.append(k)
    if rejected:
        return ControlDecision(
            action="block_reserved_env",
            ok=False,
            reason=f"runtime-reserved env rejected: {sorted(rejected)}",
        )
    return ControlDecision(
        action="allow_env",
        ok=True,
        reason="no reserved sandbox env keys",
    )


def evaluate_setup_result(*, exit_status: int) -> ControlDecision:
    if int(exit_status) != 0:
        return ControlDecision(
            action="block_setup_failed",
            ok=False,
            reason="nonzero setup_commands exit prevents agent start",
        )
    return ControlDecision(
        action="allow_setup_ok",
        ok=True,
        reason="setup commands succeeded",
    )


def evaluate_environment_status(*, status: str) -> ControlDecision:
    s = (status or "").strip().lower()
    if s == "connected":
        return ControlDecision(
            action="allow_connected",
            ok=True,
            reason="sandbox connected; live file ops permitted",
        )
    if s == "provisioning":
        return ControlDecision(
            action="wait_for_connected",
            ok=False,
            reason="setup still running; wait before file ops",
        )
    if s == "failed":
        return ControlDecision(
            action="block_environment_failed",
            ok=False,
            reason="environment failed; inspect environment.error",
        )
    return ControlDecision(
        action="block_unknown_environment_status",
        ok=False,
        reason=f"unknown environment status: {status}",
    )


def evaluate_template_network_inheritance(
    *,
    template_access: str,
    session_access: str,
) -> ControlDecision:
    rank = {"disabled": 0, "restricted": 1, "enabled": 2}
    t = (template_access or "").strip().lower()
    s = (session_access or "").strip().lower()
    if t not in rank or s not in rank:
        return ControlDecision(
            action="block_unknown_network_access",
            ok=False,
            reason="template/session network.access invalid",
        )
    if rank[s] > rank[t]:
        return ControlDecision(
            action="block_network_policy_broaden",
            ok=False,
            reason="session cannot broaden template network policy",
        )
    return ControlDecision(
        action="allow_template_network",
        ok=True,
        reason="session network is within template policy",
    )


def evaluate_budget_for_hosted(
    *,
    month_to_date_spend_usd: float,
    estimated_session_usd: float,
) -> ControlDecision:
    mtd = float(month_to_date_spend_usd)
    est = float(estimated_session_usd)
    if est < 0:
        return ControlDecision(
            action="block_invalid_estimate",
            ok=False,
            reason="estimated_session_usd must be >= 0",
        )
    if mtd + est > FLEET_MONTHLY_CAP_USD:
        return ControlDecision(
            action="block_hosted_budget",
            ok=False,
            reason=(
                f"hosted session would exceed ${FLEET_MONTHLY_CAP_USD:.0f} "
                f"fleet cap (mtd={mtd:.2f}, est={est:.2f})"
            ),
            score=mtd + est,
        )
    return ControlDecision(
        action="allow_hosted_budget",
        ok=True,
        reason="hosted session fits remaining fleet budget",
        score=FLEET_MONTHLY_CAP_USD - (mtd + est),
    )


def prefer_local_or_hosted(
    *,
    needs_isolated_linux: bool,
    needs_downloadable_outputs: bool,
    private_data: bool,
    month_to_date_spend_usd: float = 0.0,
    estimated_session_usd: float = 0.5,
) -> ControlDecision:
    if private_data and needs_isolated_linux:
        return ControlDecision(
            action="prefer_self_hosted_or_local",
            ok=True,
            reason="private data: prefer local/self-hosted over openai_hosted",
        )
    if not needs_isolated_linux:
        return ControlDecision(
            action="prefer_local_workspace",
            ok=True,
            reason="local workspace sufficient; avoid hosted container spend",
            score=1.0 if needs_downloadable_outputs else 0.0,
        )
    budget = evaluate_budget_for_hosted(
        month_to_date_spend_usd=month_to_date_spend_usd,
        estimated_session_usd=estimated_session_usd,
    )
    if not budget.ok:
        return budget
    return ControlDecision(
        action="allow_openai_hosted_session",
        ok=True,
        reason="isolated Linux needed and budget allows openai_hosted",
        score=budget.score,
    )


def validate_hosted_environment(
    *,
    network_access: str,
    allowed_domains: Sequence[str] | None,
    env: Mapping[str, str],
    month_to_date_spend_usd: float,
    estimated_session_usd: float,
    template_access: str | None = None,
) -> ControlDecision:
    net = evaluate_network_policy(
        access=network_access,
        allowed_domains=allowed_domains,
    )
    if not net.ok:
        return net
    env_d = evaluate_reserved_env(env=env)
    if not env_d.ok:
        return env_d
    if template_access:
        inh = evaluate_template_network_inheritance(
            template_access=template_access,
            session_access=network_access,
        )
        if not inh.ok:
            return inh
    return evaluate_budget_for_hosted(
        month_to_date_spend_usd=month_to_date_spend_usd,
        estimated_session_usd=estimated_session_usd,
    )


def build_session_request(
    *,
    model: str,
    input_text: str,
    inline_files: Sequence[Mapping[str, str]] | None = None,
    packages: Mapping[str, Sequence[str]] | None = None,
    setup_commands: Sequence[Mapping[str, str]] | None = None,
    env: Mapping[str, str] | None = None,
    network_access: str = "disabled",
    allowed_domains: Sequence[str] | None = None,
    environment_template_id: str | None = None,
) -> dict[str, Any]:
    env_map = dict(env or {})
    reserved = evaluate_reserved_env(env=env_map)
    if not reserved.ok:
        raise ValueError(reserved.reason)
    net = evaluate_network_policy(
        access=network_access,
        allowed_domains=allowed_domains,
    )
    if not net.ok:
        raise ValueError(net.reason)

    files: list[dict[str, Any]] = []
    for item in inline_files or []:
        files.append(
            {
                "type": "inline",
                "path": item["path"],
                "data": item["data_b64"],
            }
        )

    environment: dict[str, Any] = {
        "type": "openai_hosted",
        "network": {"access": network_access},
        "files": files,
    }
    if network_access == "restricted":
        environment["network"]["allowed_domains"] = list(allowed_domains or [])
    if packages:
        environment["packages"] = {
            k: list(v) for k, v in packages.items() if v is not None
        }
    if setup_commands:
        environment["setup_commands"] = [
            {"command": c["command"], **({"cwd": c["cwd"]} if c.get("cwd") else {})}
            for c in setup_commands
        ]
    if env_map:
        environment["env"] = env_map
    if environment_template_id:
        environment["environment_template_id"] = environment_template_id

    return {
        "agent": {"model": model},
        "environment": environment,
        "input": input_text,
        "stream": True,
        "workspace_outputs": WORKSPACE_OUTPUTS,
        "policy": {
            "wait_for_status": "connected",
            "delete_session_when_done": True,
            "retry_delete_on_409": True,
            "api_key_outside_sandbox": True,
            "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        },
        "openai_beta_header": "agents=v1",
    }


def publish_outputs_to_vault(
    *,
    vault_root: Path,
    run_id: str,
    outputs_dir: Path,
    tool_trace: Sequence[Mapping[str, Any]],
    generated_code: str,
    pre_compaction_text: str,
) -> dict[str, Any]:
    if not outputs_dir.is_dir():
        return {
            "ok": False,
            "action": "block_missing_outputs_dir",
            "reason": f"outputs_dir not found: {outputs_dir}",
        }
    artifacts: dict[str, str] = {}
    for path in sorted(outputs_dir.iterdir()):
        if path.is_file():
            artifacts[path.name] = path.read_text(encoding="utf-8")
    if not artifacts:
        return {
            "ok": False,
            "action": "block_empty_outputs",
            "reason": "no files under outputs_dir to publish",
        }
    return persist_run_artifacts(
        vault_root=vault_root,
        run_id=run_id,
        tool_trace=tool_trace,
        generated_code=generated_code,
        artifacts=artifacts,
        pre_compaction_text=pre_compaction_text,
    )


def doctor() -> dict[str, Any]:
    return {
        "ok": True,
        "module": "scripts/agent_openai_hosted_env.py",
        "docs_source": (
            "https://developers.openai.com/api/docs/guides/agents-api/"
            "environments/openai-hosted"
        ),
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "workspace_outputs": WORKSPACE_OUTPUTS,
        "default_network_access": "disabled",
        "posture": [
            "prefer_local_first",
            "hosted_only_when_isolated_linux_needed",
            "network_disabled_by_default",
            "api_key_outside_sandbox",
            "wait_for_connected",
            "publish_outputs_to_artifact_vault",
            "delete_session_when_done",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenAI-hosted sandbox environment policy"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")

    p_route = sub.add_parser("route", help="Prefer local vs openai_hosted")
    p_route.add_argument("--isolated-linux", action="store_true")
    p_route.add_argument("--outputs", action="store_true")
    p_route.add_argument("--private", action="store_true")
    p_route.add_argument("--mtd-usd", type=float, default=0.0)
    p_route.add_argument("--est-usd", type=float, default=0.5)

    p_build = sub.add_parser("build-request", help="Build a dry-run session payload")
    p_build.add_argument("--model", default="gpt-6-astra")
    p_build.add_argument("--input", required=True)
    p_build.add_argument("--network", default="disabled")
    p_build.add_argument("--domain", action="append", default=[])
    p_build.add_argument("--out", type=Path)

    p_pub = sub.add_parser("publish-outputs", help="Publish outputs dir into vault")
    p_pub.add_argument("--vault", type=Path, required=True)
    p_pub.add_argument("--run-id", required=True)
    p_pub.add_argument("--outputs-dir", type=Path, required=True)
    p_pub.add_argument("--code", type=Path, required=True)
    p_pub.add_argument("--trace-json", type=Path, required=True)
    p_pub.add_argument("--pre-text", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "doctor":
        print(json.dumps(doctor(), indent=2))
        return 0

    if args.cmd == "route":
        d = prefer_local_or_hosted(
            needs_isolated_linux=bool(args.isolated_linux),
            needs_downloadable_outputs=bool(args.outputs),
            private_data=bool(args.private),
            month_to_date_spend_usd=float(args.mtd_usd),
            estimated_session_usd=float(args.est_usd),
        )
        print(json.dumps(asdict(d), indent=2))
        return 0 if d.ok else 1

    if args.cmd == "build-request":
        req = build_session_request(
            model=args.model,
            input_text=args.input,
            network_access=args.network,
            allowed_domains=args.domain,
        )
        text = json.dumps(req, indent=2)
        if args.out:
            args.out.write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0

    if args.cmd == "publish-outputs":
        result = publish_outputs_to_vault(
            vault_root=args.vault,
            run_id=args.run_id,
            outputs_dir=args.outputs_dir,
            tool_trace=json.loads(args.trace_json.read_text(encoding="utf-8")),
            generated_code=args.code.read_text(encoding="utf-8"),
            pre_compaction_text=args.pre_text.read_text(encoding="utf-8"),
        )
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
