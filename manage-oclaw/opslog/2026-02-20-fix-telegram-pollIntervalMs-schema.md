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

- **npm update will overwrite this patch.** Must re-apply after every `npm install -g openclaw` or `npm update -g openclaw`.
- The `openclaw doctor --fix` command removes `pollIntervalMs` from config; re-add it afterward.
- v2026.2.17 added `pollIntervalMs` to an internal schema level (`z.number().int().nonnegative().optional()`) but the `.strict()` channel config schema still rejects it — **the patch is still required**.
- A non-fatal "Unrecognized key: pollIntervalMs" warning from the pre-validation check still appears in gateway logs. This does not prevent startup.

## v2026.2.17 Update (2026-02-20)

Upgraded openclaw to **v2026.2.17**. The npm install overwrote the old patched files (new hashes). The `.strict()` telegram channel config schema in v2026.2.17 **still does not include `pollIntervalMs`** — the patch had to be re-applied to the new `config-*.js` files.

### Files re-patched (v2026.2.17)

All under `/home/desazure/.npm-global/lib/node_modules/openclaw/dist/`:

| File | Change |
|------|--------|
| `config-BEpchvJh.js` | Added `pollIntervalMs` to telegram schema |
| `config-BseT0AMx.js` | Added `pollIntervalMs` to telegram schema |
| `config-CQx0LPGX.js` | Added `pollIntervalMs` to telegram schema |
| `config-F0Q6PyfW.js` | Added `pollIntervalMs` to telegram schema |

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
