# Fix: gateway crash-loop — tailscale.mode changed to invalid value "on"

**Date:** 2026-02-20 ~04:20 UTC
**Severity:** P1 — gateway down, bot unresponsive
**Duration:** ~5 min
**Affected service:** `openclaw-gateway.service` on `oclaw2026linux`

## Symptom

Gateway crash-looping after VM had been running for a few hours. SSH timed out initially (NSG rules had been cleared). After re-applying NSG and tunnel, gateway was exit code 1.

## Root Causes (two issues)

### 1. `gateway.tailscale.mode` changed to `"on"` (invalid)

The config at `~/.openclaw/openclaw.json` had:
```json
"tailscale": {
  "mode": "on",
  "resetOnExit": true
}
```

Valid values are `"off"`, `"serve"`, `"funnel"`. The value `"on"` is not a valid enum — causes hard config validation failure.

**How it changed:** Unknown. Something modified the config between our last session (when it was `"mode": "off", "resetOnExit": false`) and this crash. Possibly the gateway itself or an openclaw CLI command altered it.

**Fix:** Reset to `"mode": "off", "resetOnExit": false` via Python JSON edit.

### 2. `pollIntervalMs` schema patch still needed

The schema patch from the earlier session (adding `pollIntervalMs` to the telegram Zod schema) survived the VM reboot (files are on disk, not lost on restart). However, re-running the patch sed command created a **duplicate line**. Had to remove the duplicate.

**Lesson:** The patch sed command is not idempotent — running it twice doubles the line. Before patching, check if already applied:
```bash
grep -c pollIntervalMs /home/desazure/.npm-global/lib/node_modules/openclaw/dist/config-2b1WGSeH.js
# Should be 1 (batch only) before patching, 2 after
```

## Steps Performed

1. NSG rules re-applied (`check-setup-nsg-for-oclaw-ssh.py`) — both subnet + VM NSG
2. Tunnel restarted (old PID was stale)
3. Checked journal logs — found `gateway.tailscale.mode: Invalid input`
4. Fixed `openclaw.json`: `tailscale.mode` → `"off"`, `resetOnExit` → `false`
5. Removed duplicate `pollIntervalMs` schema line (from accidental double-patch)
6. Restarted gateway — stable, telegram provider running

## Config Guard

Watch for unexpected changes to `gateway.tailscale` in `openclaw.json`. If the gateway or CLI auto-modifies this value, it may need to be pinned or the schema patched to accept `"on"` as an alias for `"serve"`.

## Related

- Prior fix: [2026-02-20-fix-telegram-pollIntervalMs-schema.md](2026-02-20-fix-telegram-pollIntervalMs-schema.md)
- Config file: `~/.openclaw/openclaw.json` on `oclaw2026linux`
