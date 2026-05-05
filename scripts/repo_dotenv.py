"""Load repo-root `.env` into `os.environ` without clobbering real secrets.

Many shells and IDEs export empty placeholders (e.g. `APPSTORE_PRIVATE_KEY=`).
The old rule `if key not in os.environ` skipped `.env` for those keys, so scripts
never saw the real values from disk.
"""

from __future__ import annotations

import os
from pathlib import Path


def _strip_outer_quotes(value: str) -> str:
    if len(value) >= 2 and value[:2] in ('\\"', "\\'") and value.endswith(value[:2]):
        return value[2:-2]
    if value.startswith('\\"') and value.endswith('\\"'):
        return value[2:-2]
    if value.startswith("\\'") and value.endswith("\\'"):
        return value[2:-2]
    return value.strip('"').strip("'")


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
        # Handle multiline quoted values, including shell-escaped quotes copied
        # from chat/tools into `.env` as \"...\".
        quote = ""
        quote_len = 0
        if val.startswith('\\"'):
            quote = '\\"'
            quote_len = 2
        elif val.startswith("\\'"):
            quote = "\\'"
            quote_len = 2
        elif val and val[0] in ('"', "'"):
            quote = val[0]
            quote_len = 1

        if quote and not val.endswith(quote):
            parts = [val[quote_len:]]  # strip opening quote
            i += 1
            while i < len(lines):
                line = lines[i]
                if line.rstrip().endswith(quote):
                    parts.append(line.rstrip()[: -len(quote)])  # strip closing quote
                    i += 1
                    break
                parts.append(line)
                i += 1
            val = "\n".join(parts)
        else:
            val = _strip_outer_quotes(val)
            i += 1
        if key in os.environ and str(os.environ.get(key, "")).strip():
            continue
        os.environ[key] = val
