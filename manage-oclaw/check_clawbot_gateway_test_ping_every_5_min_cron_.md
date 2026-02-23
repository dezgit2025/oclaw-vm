# Gateway Watchdog: Health Check Every 5 Minutes

**Installed:** 2026-02-09
**Type:** Lightweight cron job (no LLM calls)

---

## What It Does

```
  Every 5 minutes (cron)
       |
       v
  +--------------------------------------+
  | run_gateway_watchdog.sh              |
  |                                      |
  |  1. Runs gateway_watchdog.sh         |
  |  2. Appends output to daily log      |
  |  3. Cleans logs older than 3 days    |
  +--------------------------------------+
       |
       v
  +--------------------------------------+
  | gateway_watchdog.sh                  |
  |                                      |
  |  CHECK 1: systemd unit active?       |
  |  systemctl --user is-active          |
  |  openclaw-gateway.service            |
  |       |                              |
  |       v                              |
  |  CHECK 2: TCP port 18789 open?       |
  |  timeout 1 bash /dev/tcp connect     |
  |       |                              |
  |       v                              |
  |  Both OK? → exit 0 (silent)          |
  |  Either fail? → increment counter    |
  |       |                              |
  |       v                              |
  |  2 consecutive failures?             |
  |  YES → restart gateway service       |
  |  NO  → log failure, wait for next    |
  +--------------------------------------+
```

---

## Checks Performed

| Check | Command | Pass Condition |
|-------|---------|----------------|
| systemd unit | `systemctl --user is-active openclaw-gateway.service` | Must be `active` |
| TCP port | `timeout 1 bash -c "</dev/tcp/127.0.0.1/18789"` | Must connect within 1s |

---

## Restart Logic

```
  Run 1: FAIL (count=1)
       |
       | wait 5 min
       v
  Run 2: FAIL (count=2) → threshold reached
       |
       v
  +-------------------------+
  | Rate limit check:       |
  | Last restart > 30 min?  |
  |                         |
  | YES → restart gateway   |
  | NO  → skip, log only    |
  +-------------------------+
       |
       v
  Post-restart check (5s later):
  unit active? port open?
       |
       v
  Log result
```

**Tuning parameters** (in `gateway_watchdog.sh`):

| Parameter | Value | Description |
|-----------|-------|-------------|
| `FAIL_THRESHOLD` | 2 | Consecutive failures before restart |
| `RESTART_MIN_INTERVAL_SEC` | 1800 (30 min) | Minimum time between restarts |

---

## Log Output Examples

**Healthy (silent):** No output when healthy (log only shows `---` separator)

**Failure:**
```
[2026-02-09T23:40:01Z] FAIL count=1 unit_active=0 port_open=1
```

**Recovery after failure:**
```
[2026-02-09T23:44:30Z] OK (recovered). unit=active port=open (was failing count=1)
```

**Restart triggered:**
```
[2026-02-09T23:50:00Z] FAIL count=2 unit_active=0 port_open=0
[2026-02-09T23:50:00Z] RESTARTING openclaw-gateway.service
[2026-02-09T23:50:05Z] POST-RESTART unit_active=1 port_open=1
```

**Rate-limited:**
```
[2026-02-09T23:55:00Z] SKIP restart (rate-limited). since_last_restart=300s
```

---

## How to Check the Gateway

### Quick status

```bash
# From local machine (via SSH)
ssh oclaw "systemctl --user status openclaw-gateway.service --no-pager"

# Check port is listening
ssh oclaw "ss -tlnp | grep 18789"

# Test HTTP (via tunnel)
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18792/
```

### Check watchdog logs

```bash
# Today's log
ssh oclaw "cat ~/.openclaw/logs/gateway-watchdog/$(date -u +%Y-%m-%d).log"

# All recent logs
ssh oclaw "ls -lh ~/.openclaw/logs/gateway-watchdog/"

# Tail live
ssh oclaw "tail -f ~/.openclaw/logs/gateway-watchdog/$(date -u +%Y-%m-%d).log"
```

### Check watchdog state

```bash
# Current failure count and last restart timestamp
ssh oclaw "cat ~/.local/state/openclaw/gateway-watchdog.state"
# Format: <fail_count> <last_restart_epoch>
# "0 0" = healthy, no recent restart
```

### Run watchdog manually

```bash
# Test the check (does not affect cron schedule)
ssh oclaw "bash ~/.openclaw/workspace/manage-oclaw/gateway_watchdog.sh"
```

### Check cron is installed

```bash
ssh oclaw "crontab -l | grep watchdog"
# Expected: */5 * * * * /home/desazure/.openclaw/workspace/manage-oclaw/run_gateway_watchdog.sh
```

---

## Gateway Troubleshooting

### Gateway is down

```bash
# Check status
ssh oclaw "systemctl --user status openclaw-gateway.service --no-pager"

# Check logs
ssh oclaw "journalctl --user -u openclaw-gateway.service --no-pager -n 50"

# Manual restart
ssh oclaw "systemctl --user restart openclaw-gateway.service"

# Verify after restart
ssh oclaw "systemctl --user is-active openclaw-gateway.service && ss -tlnp | grep 18789"
```

### Gateway keeps crashing

```bash
# Check for OOM or repeated restarts
ssh oclaw "journalctl --user -u openclaw-gateway.service --no-pager --since '1 hour ago' | grep -i 'start\|stop\|fail\|error\|oom'"

# Check memory usage
ssh oclaw "systemctl --user status openclaw-gateway.service | grep Memory"

# Check watchdog restart history
ssh oclaw "grep RESTART ~/.openclaw/logs/gateway-watchdog/*.log"
```

### Port 18789 not reachable from local (via tunnel)

```bash
# Check tunnel is running
/Users/dez/Projects/openclaw_vm/manage-oclaw/create-manage-tunnel-oclaw.py status

# Gateway binds to 0.0.0.0:18789 but tunnel forwards 18792
# Port mapping:
#   Local 18792 → VM 18792 (gateway HTTP)
#   VM 18789 = gateway listen port (direct, not tunneled)
#   VM 18792 = gateway API port (tunneled)

# Test via tunnel
curl -I http://127.0.0.1:18792/
```

---

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| Watchdog script | `VM: ~/.openclaw/workspace/manage-oclaw/gateway_watchdog.sh` | Health check + restart logic |
| Runner wrapper | `VM: ~/.openclaw/workspace/manage-oclaw/run_gateway_watchdog.sh` | Logging + cleanup wrapper |
| Daily logs | `VM: ~/.openclaw/logs/gateway-watchdog/YYYY-MM-DD.log` | Watchdog output (auto-cleaned after 3 days) |
| State file | `VM: ~/.local/state/openclaw/gateway-watchdog.state` | Fail count + last restart timestamp |
| Cron entry | `crontab -l` | `*/5 * * * *` schedule |
| This doc | `local: manage-oclaw/check_clawbot_gateway_test_ping_every_5_min_cron_.md` | |

---

## Resource Usage

Minimal:
- `systemctl --user is-active` = instant
- TCP connect = 1s max timeout
- No LLM calls, no HTTP requests to external APIs
- Logs auto-cleaned after 3 days
