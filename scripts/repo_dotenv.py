"""Load repo-root `.env` into `os.environ` without clobbering real secrets.

Many shells and IDEs export empty placeholders (e.g. `APPSTORE_PRIVATE_KEY=`).
The old rule `if key not in os.environ` skipped `.env` for those keys, so scripts
never saw the real values from disk.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_repo_dotenv(repo_root: Path) -> None:
    env_path = repo_root / ".env"
    if not env_path.is_file():
        return
    lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or s.startswith("#") or "=" not in s:
            i += 1
            continue
        k, _, v = s.partition("=")
        key = k.strip()
        if not key:
            i += 1
            continue
        val = v.strip()
        # Handle multiline quoted values (double or single quotes)
        if val and val[0] in ('"', "'") and not val.endswith(val[0]):
            quote = val[0]
            parts = [val[1:]]  # strip opening quote
            i += 1
            while i < len(lines):
                line = lines[i]
                if line.rstrip().endswith(quote):
                    parts.append(line.rstrip()[:-1])  # strip closing quote
                    i += 1
                    break
                parts.append(line)
                i += 1
            val = "\n".join(parts)
        else:
            val = val.strip('"').strip("'")
            i += 1
        if key in os.environ and str(os.environ.get(key, "")).strip():
            continue
        os.environ[key] = val
