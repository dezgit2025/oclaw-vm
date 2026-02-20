# Tailscale Exit Node Rules — oclaw VM

## Overview

The oclaw VM (`oclaw2026linux`) uses a Tailscale exit node to route all internet traffic through a residential IP address. This avoids 403 blocks that many services apply to Azure datacenter IPs.

## Architecture

```
oclaw VM (100.111.79.93)
    │
    │  all internet traffic via Tailscale tunnel
    ▼
chromeos-nissa (100.124.62.63) ── residential IP (108.29.69.37)
    │
    ▼
  Internet
```

**Fallback (exit node down):**

```
oclaw VM (100.111.79.93)
    │
    │  direct Azure egress
    ▼
  Internet ── Azure IP (20.81.190.88)
```

## Primary Exit Node: chromeos-nissa

| Property | Value |
|----------|-------|
| Device | chromeos-nissa (Android/ChromeOS) |
| Tailscale IP | `100.124.62.63` |
| Residential IP | `108.29.69.37` |
| Role | Primary exit node for all VM internet traffic |

### How it's set

```bash
sudo tailscale set --exit-node=chromeos-nissa
```

### How to verify

```bash
# Check exit node is active
tailscale status
# Should show: chromeos-nissa ... active; exit node; direct ...

# Check egress IP is residential
curl -s ifconfig.me
# Should return: 108.29.69.37
```

## Failover: Watchdog Script

A cron-based watchdog automatically handles exit node failures and recovery.

### How it works

```
Every 2 minutes (cron):
    │
    ├─ Ping chromeos-nissa via `tailscale ping`
    │
    ├─ Reachable?
    │   ├─ YES + exit node active    → do nothing (healthy)
    │   ├─ YES + exit node inactive  → re-enable chromeos-nissa
    │   └─ NO                        → increment failure counter
    │
    └─ 2 consecutive failures?
        ├─ YES → FAILOVER: clear exit node → Azure native egress
        └─ NO  → wait for next check
```

### Failover behavior

| Condition | Action | Egress IP |
|-----------|--------|-----------|
| chromeos-nissa reachable | Use as exit node | `108.29.69.37` (residential) |
| 1 ping failure | Log warning, wait | `108.29.69.37` (still active) |
| 2 consecutive failures | Clear exit node | `20.81.190.88` (Azure) |
| chromeos-nissa recovers | Re-enable exit node | `108.29.69.37` (residential) |

### Failover timing

- Check interval: **2 minutes** (cron)
- Failure threshold: **2 consecutive failures**
- Time to failover: **~4 minutes** (worst case)
- Time to restore: **~2 minutes** (next successful ping)

### Files

| File | Purpose |
|------|---------|
| `~/.openclaw/workspace/ops/watchdog/tailscale_egress_watchdog.py` | Watchdog script |
| `~/.openclaw/workspace/ops/watchdog/run_tailscale_egress_watchdog.sh` | Cron runner (logs to daily file) |
| `~/.local/state/openclaw/tailscale-egress-watchdog.state` | State file (JSON) |
| `~/.openclaw/logs/tailscale-egress-watchdog/YYYY-MM-DD.log` | Daily logs |

### State file format

```json
{
  "consecutive_failures": 0,
  "exit_node_active": true,
  "last_transition": "2026-02-20T06:15:00Z restored chromeos-nissa"
}
```

### Manual checks

```bash
# Watchdog state
cat ~/.local/state/openclaw/tailscale-egress-watchdog.state

# Today's watchdog logs
cat ~/.openclaw/logs/tailscale-egress-watchdog/$(date -u +%Y-%m-%d).log

# Cron entry
crontab -l | grep tailscale
```

## IMDS Route Exception

The exit node routes ALL traffic, including Azure IMDS (`169.254.169.254`). This breaks the Foundry MI proxy which needs IMDS for Managed Identity tokens.

**Fix (already applied and persisted):**

```bash
sudo ip rule add to 169.254.169.254 lookup main priority 100
```

Persisted via: `/etc/networkd-dispatcher/routable.d/50-imds-route.sh`

**Without this rule, all LLM calls fail with HTTP 500.**

## Rules — Do and Do NOT

### DO

- Keep chromeos-nissa **powered on and awake** for residential egress
- Let the watchdog handle failover automatically
- Verify egress IP after VM restart: `curl -s ifconfig.me`
- Check watchdog state if bot seems slow or getting 403 errors

### DO NOT

- **Never advertise oclaw as an exit node** (`tailscale set --advertise-exit-node`) — Tailscale cannot use and be an exit node at the same time. This command clears the chromeos-nissa exit node, dropping residential egress and exposing the VM to 403 blocks
- **Never manually clear the exit node** without the watchdog — it will re-enable chromeos-nissa on the next successful ping anyway
- **Never set `tailscale.mode`** in `openclaw.json` to anything other than `"off"` — this is the gateway's own Tailscale setting, unrelated to SSH/egress

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Bot responds but slow | Exit node latency or sleeping device | Check `tailscale status`, wake chromeos-nissa |
| Bot not responding, "typing" | Foundry proxy 500 (IMDS routing) | Verify `ip rule show` has 169.254.169.254 rule |
| 403 errors from external APIs | Azure IP egress (exit node down) | Check watchdog state, wake chromeos-nissa |
| `tailscale ping` times out | Device asleep or offline | Power on chromeos-nissa, watchdog will restore |
| Egress IP shows `20.81.190.88` | Exit node cleared (failover active) | Wake chromeos-nissa, watchdog restores in ~2 min |
