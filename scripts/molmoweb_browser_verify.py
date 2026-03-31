#!/usr/bin/env python3
"""Run a local MolmoWeb browser-agent query and save a trajectory artifact."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def resolve_molmoweb_home(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()

    env_value = os.environ.get("MOLMOWEB_HOME")
    if env_value:
        return Path(env_value).expanduser().resolve()

    return (Path.home() / "molmoweb").resolve()


def slugify_query(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "run"


def default_output_path(query: str) -> Path:
    return Path("evidence") / "molmoweb" / f"{slugify_query(query)}.html"


def resolve_molmoweb_python(molmoweb_home: Path) -> Path:
    candidate = molmoweb_home / ".venv" / "bin" / "python"
    if candidate.is_file():
        return candidate
    return Path(sys.executable)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute a MolmoWeb browser-agent run against a running local server.",
    )
    parser.add_argument("--query", required=True, help="Natural-language browser task to run.")
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("MOLMOWEB_ENDPOINT", "http://127.0.0.1:8001"),
        help="MolmoWeb FastAPI endpoint.",
    )
    parser.add_argument(
        "--molmoweb-home",
        default=None,
        help="Path to the local molmoweb checkout. Defaults to $MOLMOWEB_HOME or ~/molmoweb.",
    )
    parser.add_argument("--steps", type=int, default=8, help="Maximum agent steps.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output HTML path. Defaults to evidence/molmoweb/<slug>.html",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run the local browser in headed mode instead of headless mode.",
    )
    parser.add_argument(
        "--server-checkpoint",
        default=None,
        help="Override the local checkpoint path used when auto-starting the server.",
    )
    parser.add_argument(
        "--no-auto-start-server",
        action="store_true",
        help="Fail instead of auto-starting the local MolmoWeb server when the endpoint is down.",
    )
    return parser


def is_server_ready(endpoint: str) -> bool:
    health_url = endpoint.rstrip("/") + "/openapi.json"
    try:
        with urlopen(health_url, timeout=2) as response:
            return response.status == 200
    except (OSError, URLError):
        return False


def auto_start_server(
    molmoweb_home: Path,
    runner: Path,
    endpoint: str,
    checkpoint: str | None,
) -> subprocess.Popen[bytes]:
    parsed = urlsplit(endpoint)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8001
    if host not in {"127.0.0.1", "localhost"}:
        raise SystemExit(f"Auto-start only supports local endpoints, got: {endpoint}")

    ckpt = checkpoint or "./checkpoints/MolmoWeb-4B-infer"
    log_dir = ROOT / "evidence" / "molmoweb"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "molmoweb-server.log"
    log_file = log_path.open("ab")
    process = subprocess.Popen(
        [str(runner), "-m", "uvicorn", "agent.fastapi_model_server:app", "--host", host, "--port", str(port)],
        cwd=str(molmoweb_home),
        env={
            **os.environ,
            "CKPT": ckpt,
            "PREDICTOR_TYPE": "hf",
            "PORT": str(port),
        },
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    deadline = time.time() + 180
    while time.time() < deadline:
        if process.poll() is not None:
            raise SystemExit(f"MolmoWeb server exited early. See {log_path}")
        if is_server_ready(endpoint):
            return process
        time.sleep(2)

    process.terminate()
    raise SystemExit(f"Timed out waiting for MolmoWeb server. See {log_path}")


def _summary_footer_code() -> str:
    return """
saved_path = Path(traj.save_html(output_path={output_path!r}, query=query)).resolve()
print(f"TRAJ_HTML={{saved_path}}")
print(f"STEPS={{len(traj.steps)}}")
last = traj.steps[-1] if traj.steps else None
print(f"LAST_ERROR={{last.error if last else None}}")
print(f"LAST_PRED={{last.prediction.action if last and last.prediction else None}}")
""".strip()


def main() -> int:
    args = build_parser().parse_args()

    molmoweb_home = resolve_molmoweb_home(args.molmoweb_home)
    if not molmoweb_home.is_dir():
        raise SystemExit(f"MolmoWeb checkout not found: {molmoweb_home}")

    output_path = Path(args.output) if args.output else default_output_path(args.query)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    runner = resolve_molmoweb_python(molmoweb_home)
    started_server = None
    if not is_server_ready(args.endpoint):
        if args.no_auto_start_server:
            raise SystemExit(f"MolmoWeb server is not reachable at {args.endpoint}")
        started_server = auto_start_server(
            molmoweb_home=molmoweb_home,
            runner=runner,
            endpoint=args.endpoint,
            checkpoint=args.server_checkpoint,
        )

    code = """
from pathlib import Path
from inference import MolmoWeb

client = MolmoWeb(endpoint={endpoint!r}, local=True, headless={headless}, verbose=True)
try:
    query = {query!r}
    traj = client.run(query=query, max_steps={steps})
    {summary_footer}
finally:
    client.close()
""".format(
        endpoint=args.endpoint,
        headless=not args.headed,
        query=args.query,
        steps=args.steps,
        output_path=str(output_path),
        summary_footer=_summary_footer_code(),
    )

    subprocess.run(
        [str(runner), "-c", code],
        cwd=str(molmoweb_home),
        check=True,
    )
    if started_server is not None:
        print(f"SERVER_STARTED_PID={started_server.pid}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
