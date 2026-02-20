# Fix: openclaw gateway crash-loop — telegram pollIntervalMs schema rejection

**Date:** 2026-02-20
**Severity:** P1 — gateway down, bot unresponsive to Telegram
**Duration:** ~25 min (detected 01:13 UTC, resolved 01:20 UTC)
**Affected service:** `openclaw-gateway.service` on `oclaw2026linux`

## Symptom

Bot stopped responding to Telegram pings. Gateway was crash-looping (140+ restart cycles) with exit code 1.

## Root Cause

Config key `channels.telegram.pollIntervalMs` was present in `~/.openclaw/openclaw.json` (set to `15000`), written by openclaw **v2026.2.2-3**. After the gateway binary was updated to **v2026.2.9**, the new Zod schema uses `.strict()` validation on the telegram channel config and no longer recognizes `pollIntervalMs` — causing a hard config validation failure on startup.

The service unit file still references `v2026.2.2-3` in its description, but the actual binary at `/home/desazure/.npm-global/lib/node_modules/openclaw/dist/index.js` is `v2026.2.9`.

## Fix Applied

Patched the Zod schema in the installed openclaw dist to re-add `pollIntervalMs` as a valid optional field for the telegram channel schema only.

### Files modified (on VM)

All under `/home/desazure/.npm-global/lib/node_modules/openclaw/dist/`:

| File | Change |
|------|--------|
| `config-2b1WGSeH.js` | Added `pollIntervalMs` to telegram schema |
| `config-Bm_vQzVn.js` | Added `pollIntervalMs` to telegram schema |
| `config-CuE2AFLW.js` | Added `pollIntervalMs` to telegram schema |
| `config-Cz6PlSb8.js` | Added `pollIntervalMs` to telegram schema |

### Exact patch (applied to each file)

Added this line after the `streamMode` enum block (unique to telegram schema):

```js
// Before:
	]).optional().default("partial"),
	mediaMaxMb: z.number().positive().optional(),

// After:
	]).optional().default("partial"),
	pollIntervalMs: z.number().int().positive().optional(),
	mediaMaxMb: z.number().positive().optional(),
```

The `streamMode` field only exists in the telegram channel schema, so this anchor ensures no other channel schemas (whatsapp, discord, slack, etc.) were touched.

### What was NOT patched

A separate pre-validation check in `index.js` / the gateway CLI entry point still logs a warning:
```
Invalid config at ~/.openclaw/openclaw.json: channels.telegram: Unrecognized key: "pollIntervalMs"
```
This warning is **non-fatal** — the gateway starts and runs fine despite it.

## Caveats

- ~~**npm update will overwrite this patch.**~~ **RESOLVED:** As of v2026.2.17, `pollIntervalMs` is natively supported in the telegram Zod schema (`z.number().int().nonnegative().optional()`). The manual patch is no longer needed.
- The `openclaw doctor --fix` command (run during v2026.2.17 upgrade) removed `pollIntervalMs` from config; it was re-added afterward set to `10000` (10s).

## Resolution (2026-02-20)

Upgraded openclaw to **v2026.2.17** which includes `pollIntervalMs` natively in the telegram schema. The manual dist patches to `config-*.js` files are no longer present or needed. The config key `pollIntervalMs: 10000` is set in `openclaw.json` and validated without warnings.

## Follow-up Changes (same session)

### 1. pollIntervalMs changed 15s → 10s

Changed `channels.telegram.pollIntervalMs` from `15000` to `10000` in `~/.openclaw/openclaw.json` to reduce Telegram long-poll latency (default is 30s).

### 2. Session store lock deadlock after restart

After the schema fix, the gateway was running but the telegram handler was failing with:
```
[telegram] handler failed: Error: timeout acquiring session store lock:
  /home/desazure/.openclaw/agents/main/sessions/sessions.json.lock
```

**Cause:** Stale lock file left over from the crash-loop (140+ restarts). The lock was held by the current PID itself — a self-deadlock.

**Fix:** Restarted the gateway cleanly (SIGTERM → full shutdown → start). The lock file was released on graceful shutdown, and the fresh process started without lock contention.

**Lesson:** After a prolonged crash-loop, always do a clean restart even if the gateway appears to be running — stale lock files from prior crash cycles can persist.

## Verification

```bash
# Gateway stayed running after patch
ssh oclaw "systemctl --user status openclaw-gateway.service --no-pager"
# Active: active (running), telegram provider started, heartbeat running
```

## Related

- Config file: `~/.openclaw/openclaw.json` on `oclaw2026linux`
- `pollIntervalMs: 10000` controls Telegram long-polling interval (changed from 15s → 10s; openclaw default is 30s)
- Gateway watchdog cron detected the failure but couldn't fix it (config error, not a transient crash)
