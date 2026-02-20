# what-oclaw-gateway-does

## What the OpenClaw gateway does
The **OpenClaw gateway** is the main always-on daemon that makes OpenClaw work.

It:
- **Receives messages/events** from your channels (Telegram, etc.)
- **Maintains session state** (reads/writes session `.jsonl` logs, manages what context gets sent)
- **Runs the agent loop** (calls the model provider, routes tool calls, streams results)
- **Executes tools** (shell commands, browser control, Google/ClickUp skills, cron jobs, etc.)
- **Hosts local endpoints** OpenClaw uses (e.g., the websocket/http service on port **18789**)

If the gateway is down or wedged, OpenClaw looks **silent** because nothing is reading Telegram updates or generating replies.

### Related service (not the gateway)
- `openclaw-foundry-proxy.service` (port **18791**) is the **Azure AI Foundry Managed Identity proxy**. The gateway uses it for Foundry calls, but it’s not the component that talks to Telegram.

## Restarting the gateway
Preferred:
```bash
openclaw gateway restart
```
Equivalent systemd command:
```bash
systemctl --user restart openclaw-gateway.service
```
Check status:
```bash
openclaw status
openclaw gateway status
systemctl --user status openclaw-gateway.service --no-pager
```

## Cron job check we just did (watchdog + existing session GC)
Current user crontab includes:

```cron
# OpenClaw session log GC (backup >5MB, truncate to ~3MB)
TZ=America/New_York
0 20 * * * /home/desazure/.openclaw/workspace/manage-oclaw/run_session_gc.sh

# OpenClaw gateway watchdog (no LLM). Every 5 minutes. Logs cleaned after 3 days.
*/5 * * * * /home/desazure/.openclaw/workspace/manage-oclaw/run_gateway_watchdog.sh
```

### Watchdog behavior (no LLM test)
- Checks:
  - `systemctl --user is-active openclaw-gateway.service`
  - TCP connect to `127.0.0.1:18789`
- If **2 consecutive failures**, it restarts the gateway via:
  - `systemctl --user restart openclaw-gateway.service`
- Rate limit: at most once per **30 minutes** (prevents flapping)

### Watchdog logs
- Directory: `~/.openclaw/logs/gateway-watchdog/`
- Files: `~/.openclaw/logs/gateway-watchdog/YYYY-MM-DD.log` (UTC date)
- Logs are automatically deleted when older than **3 days**.

---
Saved for: Poonie (2026-02-09)
