---
name: callstack-agent-device-roi
description: Steal high-ROI Callstack agent-device patterns (proxy, PR runtime evidence) for native Random Timer without RN/Expo spend.
---

# Callstack agent-device ROI (Random Timer)

Source: Callstack Incubator Aug 2026 dispatch (`~/Downloads/callstack.pdf`, 2026-09-14).

Random Timer is **native** Kotlin/Swift — skip RN/Rozenite/Margelo/React Navigation. Implement only transferable agent infrastructure.

## Do (high ROI, $0)

1. Runtime evidence before UI "done":
   ```bash
   python3 scripts/agent_device_doctor.py --json
   ./scripts/device-tests/agent-device-pr-evidence.sh
   ```
2. Self-host proxy on a Mac with Simulator (prefer SSH `-L` / Tailscale; not paid ngrok):
   ```bash
   ./scripts/device-tests/agent-device-proxy-host.sh
   # agent machine:
   ssh -L 4310:127.0.0.1:4310 <device-host>
   export AGENT_DEVICE_DAEMON_AUTH_TOKEN=...
   export AGENT_DEVICE_DAEMON_BASE_URL=http://127.0.0.1:4310/agent-device
   ./scripts/device-tests/agent-device-proxy-connect.sh
   ```
3. Rule: green unit CI ≠ mobile still works (Callstack blog theme). Cite screenshot + snapshot paths in PRs.

## Do not (low ROI / budget)

- Expo EAS cloud simulators waitlist
- Paid Apex GA / Agent Conf tickets
- React Native 0.87 upgrades, Rozenite plugins, Nitro/MMKV

## Related

- `docs/DEVICE_E2E_TESTS.md`
- `scripts/agent_device_doctor.py`
- Existing CI lane: `scripts/device-tests/ci-maestro-ios.sh`
