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
# cwd-aware dispatcher: Random-Timer uses bin/pi-yolo; RealEstate uses ./pi-yolo
set -euo pipefail
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  R="\$(git rev-parse --show-toplevel)"
  if [[ -x "\$R/bin/pi-yolo" ]]; then
    exec env PI_YOLO_ROOT="\$R" "\$R/bin/pi-yolo" "\$@"
  fi
  if [[ -x "\$R/pi-yolo" ]]; then
    exec env PI_YOLO_ROOT="\$R" "\$R/pi-yolo" "\$@"
  fi
fi
R="\${PI_YOLO_ROOT:-$ROOT}"
exec env PI_YOLO_ROOT="\$R" "\$R/bin/pi-yolo" "\$@"
EOF
chmod +x "$TARGET"
echo "installed $TARGET (cwd-aware; fallback $ROOT/bin/pi-yolo)"
# Smoke from this repo only — do not require RealEstate doctor.
(cd "$ROOT" && "$TARGET" doctor --json)
