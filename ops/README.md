# clawbot ops folder

This folder contains small, local operational helpers that keep OpenClaw/clawbot reliable (session GC, gateway watchdog, etc.).

## Layout

- `watchdog/`
  - `gateway_watchdog.sh` — checks gateway unit + port; triggers restart on consecutive failures (rate-limited)
  - `restart_gateway.py` — performs `systemctl --user restart openclaw-gateway.service` with structured log output
  - `run_gateway_watchdog.sh` — wrapper for cron: sets DBus env for `systemctl --user`, appends to log, deletes logs >3 days

- `session-gc/`
  - `session_gc.py` — backs up oversized `*.jsonl` then truncates oldest lines to target size (preserves header)
  - `run_session_gc.sh` — wrapper that logs to `~/.openclaw/logs/session-gc.log`

- `docs/` — human notes

## Logs

- Gateway watchdog: `~/.openclaw/logs/gateway-watchdog/YYYY-MM-DD.log`
- Session GC: `~/.openclaw/logs/session-gc.log`

## Cron

Installed in user crontab:

- Session GC: daily 8:00 PM America/New_York
  - `/home/desazure/.openclaw/workspace/ops/session-gc/run_session_gc.sh`

- Gateway watchdog: every 5 minutes
  - `/home/desazure/.openclaw/workspace/ops/watchdog/run_gateway_watchdog.sh`

## Manual run

```bash
/home/desazure/.openclaw/workspace/ops/watchdog/run_gateway_watchdog.sh
/home/desazure/.openclaw/workspace/ops/session-gc/run_session_gc.sh
```

## Quick health checks

```bash
openclaw gateway status
systemctl --user status openclaw-gateway.service
journalctl --user -u openclaw-gateway.service --since '1 hour ago' --no-pager | tail -n 200
```
