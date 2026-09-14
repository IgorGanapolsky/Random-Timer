#!/usr/bin/env bash
# run-ios-vphone.sh — Optional virtual-iPhone lane via vphone-cli.
# Prefer this (or Simulator) over the CEO physical phone.
# Never claim device E2E success unless Maestro exits 0 after doctor status=ready_for_launch.
#
# Usage:
#   ./scripts/device-tests/run-ios-vphone.sh [--vm NAME] [--smoke-only] [--json-doctor]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

VM_NAME="${VPHONE_VM:-rtt-qa}"
SMOKE_ONLY=0
JSON_DOCTOR=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --vm)
      VM_NAME="$2"
      shift 2
      ;;
    --smoke-only)
      SMOKE_ONLY=1
      shift
      ;;
    --json-doctor)
      JSON_DOCTOR=1
      shift
      ;;
    -h|--help)
      sed -n '1,12p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 64
      ;;
  esac
done

DOCTOR_JSON="$(python3 scripts/vphone_doctor.py --json)"
if [[ "$JSON_DOCTOR" -eq 1 ]]; then
  echo "$DOCTOR_JSON"
fi

STATUS="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])' <<<"$DOCTOR_JSON")"
CLAIM="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["claim_device_e2e_on_vphone"])' <<<"$DOCTOR_JSON")"

echo "vphone_doctor.status=$STATUS"
echo "vphone_doctor.claim_device_e2e_on_vphone=$CLAIM"

case "$STATUS" in
  ready_for_launch|ready_for_vm_create)
    ;;
  blocked_sip_amfi|blocked_cli_missing|blocked_not_apple_silicon)
    echo "vphone lane blocked ($STATUS). Falling back to iOS Simulator Maestro." >&2
    echo "Evidence: python3 scripts/vphone_doctor.py --json" >&2
    if [[ "$SMOKE_ONLY" -eq 1 ]]; then
      exec bash scripts/device-tests/run-ios-simulator.sh --maestro --smoke-only
    fi
    exec bash scripts/device-tests/run-ios-simulator.sh --maestro
    ;;
  *)
    echo "Unknown doctor status: $STATUS" >&2
    exit 2
    ;;
esac

if [[ "$STATUS" == "ready_for_vm_create" ]]; then
  echo "Host is ready for VM create, but no VM exists yet." >&2
  echo "Create once (CEO SIP gate already satisfied): vphone-cli vm create ${VM_NAME} -V regular" >&2
  echo "Then re-run this script. Not claiming device E2E." >&2
  exit 2
fi

# ready_for_launch: boot VM, then document connection — Maestro pairing to PV guests
# is host-dependent; fail closed if we cannot prove Maestro exit 0.
if ! command -v vphone-cli >/dev/null 2>&1; then
  echo "vphone-cli missing despite doctor ready status" >&2
  exit 2
fi

echo "Launching VM: $VM_NAME"
vphone-cli vm launch "$VM_NAME" || {
  echo "vm launch failed — not claiming device E2E" >&2
  exit 1
}

INFO_JSON="$(vphone-cli vm info "$VM_NAME" --json 2>/dev/null || true)"
echo "vm.info=${INFO_JSON:-unavailable}"

if ! command -v maestro >/dev/null 2>&1; then
  echo "Maestro not on PATH after VM launch — not claiming device E2E" >&2
  exit 1
fi

# Prefer explicit device id from env when agents wire SSH/VNC tunnels.
DEVICE_ID="${VPHONE_MAESTRO_DEVICE:-}"
FLOW=".maestro/ios-smoke-test.yaml"
if [[ ! -f "$FLOW" ]]; then
  echo "Missing flow: $FLOW" >&2
  exit 1
fi

set +e
if [[ -n "$DEVICE_ID" ]]; then
  maestro test -p ios --device "$DEVICE_ID" "$FLOW"
  RC=$?
else
  echo "VPHONE_MAESTRO_DEVICE unset. VM launched; Maestro device binding not verified." >&2
  echo "Connect via VNC/SSH per upstream docs, set VPHONE_MAESTRO_DEVICE, re-run." >&2
  echo "Not claiming device E2E (no Maestro EXIT=0)." >&2
  RC=1
fi
set -e

if [[ "$RC" -ne 0 ]]; then
  echo "Maestro did not exit 0 (rc=$RC). claim_device_e2e_on_vphone remains false." >&2
  exit "$RC"
fi

echo "Maestro EXIT=0 on vphone device=$DEVICE_ID flow=$FLOW"
exit 0
