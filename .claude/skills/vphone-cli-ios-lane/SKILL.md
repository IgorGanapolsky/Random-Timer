---
name: vphone-cli-ios-lane
description: Prefer Lakr233/vphone-cli virtual iPhone (or Simulator) over the CEO physical phone for Random Timer iOS E2E; run vphone_doctor and fail closed on SIP/AMFI.
---

# vphone-cli iOS lane

Upstream: https://github.com/Lakr233/vphone-cli (MIT). Boots a virtual iPhone via Apple Virtualization.framework (PCC research VM).

## When to use

- Any iOS device E2E, paywall smoke, timer completion, StoreKit sandbox QA
- Before touching or leasing the CEO physical iPhone
- When `never-contend-for-the-phone` / device-e2e skills apply

## Hard rules

1. Run `python3 scripts/vphone_doctor.py --json` first. Cite `status` + `blockers`.
2. Prefer order: **vphone (when ready)** → **iOS Simulator + Maestro** → never CEO handset.
3. Do **not** disable SIP / set AMFI boot-args without explicit CEO risk acceptance.
4. Prefer variants `less` or `regular` for app QA. Use `jb`/`exp` only when sideload/research is required.
5. Never claim device E2E on vphone unless `claim_device_e2e_on_vphone` is true **and** Maestro exits 0.
6. If status is `blocked_sip_amfi` or `blocked_cli_missing`, run Simulator fallback:
   `./scripts/device-tests/run-ios-simulator.sh --maestro --smoke-only`

## Commands

```bash
python3 scripts/vphone_doctor.py --json
./scripts/device-tests/run-ios-vphone.sh --smoke-only
# After SIP Option B + amfidont + VM create:
# vphone-cli vm create rtt-qa -V regular
# vphone-cli vm launch rtt-qa
# VPHONE_MAESTRO_DEVICE=<id> ./scripts/device-tests/run-ios-vphone.sh --vm rtt-qa --smoke-only
```

## SIP gate (CEO only)

- Option B (minimal): Recovery `csrutil enable --without debug` + `csrutil allow-research-guests enable`, then `vphone-amfidont`
- Option A (most permissive): Recovery `csrutil disable` + allow-research-guests, then `nvram boot-args` with `amfi_get_out_of_my_way=1`

Agents install the cask and doctor wiring only; they do not flip SIP.

## Product value

Isolated Random Timer paywall/timer smoke without contending for the CEO handset. Keeps agent loops unblocked when Simulator pairing works; unlocks closer-to-device PV guests when CEO accepts the SIP gate.
