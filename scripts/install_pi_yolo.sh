#!/usr/bin/env bash
# Install Random-Timer pi-yolo into ~/.local/bin (does not touch other repos).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HOME/.local/bin"
TARGET="$HOME/.local/bin/pi-yolo"
# Never write through a symlink into another project.
if [[ -L "$TARGET" ]]; then
  rm -f "$TARGET"
fi
cat > "$TARGET" <<EOF
#!/usr/bin/env bash
set -euo pipefail
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  R="\$(git rev-parse --show-toplevel)"
  if [[ -f "\$R/bin/pi-yolo" ]]; then
    exec env PI_YOLO_ROOT="\$R" "\$R/bin/pi-yolo" "\$@"
  fi
fi
R="\${PI_YOLO_ROOT:-$ROOT}"
exec env PI_YOLO_ROOT="\$R" "\$R/bin/pi-yolo" "\$@"
EOF
chmod +x "$TARGET"
echo "installed $TARGET -> $ROOT/bin/pi-yolo"
"$TARGET" doctor --json
