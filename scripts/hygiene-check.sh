#!/usr/bin/env bash
# Back-compat shim: hooks and docs may still call scripts/hygiene-check.sh
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/shell/hygiene-check.sh" "$@"
