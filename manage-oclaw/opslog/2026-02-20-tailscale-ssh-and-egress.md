# Tailscale: SSH transport + residential IP egress

**Date:** 2026-02-20
**Severity:** Improvement — eliminates daily NSG maintenance + fixes 403 blocks
**Affected:** SSH connectivity, VM internet egress

## What Changed

### 1. SSH now uses Tailscale instead of public IP

- Installed Tailscale v1.94.2 on `oclaw2026linux`
- `~/.ssh/config` updated: `oclaw` → `100.111.79.93` (Tailscale IP)
- Old public IP entry preserved as `oclaw-public` (emergency fallback)
- `tailscaled.service` enabled — starts on boot, reconnects automatically
- **NSG script no longer needed for daily operations**

### 2. Exit node for residential IP egress

- `chromeos-nissa` (Android, `100.124.62.63`) configured as Tailscale exit node
- VM egresses internet traffic through residential IP `108.29.69.37`
- Solves 403 blocks from services that reject Azure datacenter IPs

### 3. Exit node failover watchdog

- Script: `~/.openclaw/workspace/ops/watchdog/tailscale_egress_watchdog.py`
- Runner: `~/.openclaw/workspace/ops/watchdog/run_tailscale_egress_watchdog.sh`
- Cron: every 2 minutes
- State: `~/.local/state/openclaw/tailscale-egress-watchdog.state`
- Logs: `~/.openclaw/logs/tailscale-egress-watchdog/YYYY-MM-DD.log`
- Behavior: 2 consecutive ping failures → clears exit node (Azure fallback); re-enables when exit node recovers

### 4. Tailscale ACLs

Configured at https://login.tailscale.com/admin/acls:

| Source | Destination | Allowed |
|--------|-------------|---------|
| MacBook (`100.85.14.32`) | oclaw (`100.111.79.93`) | Yes |
| oclaw | chromeos-nissa (`100.124.62.63`) | Yes |
| MacBook / oclaw | Internet (via exit node) | Yes |
| oclaw → MacBook | | **Blocked** |
| iPhone → oclaw | | **Blocked** |

## New Startup Workflow

```bash
az vm start --name oclaw2026linux --resource-group RG_OCLAW2026
./manage-oclaw/create-manage-tunnel-oclaw.py start
# Done — no NSG step
```

## Tailnet Nodes

| Node | Tailscale IP | Role |
|------|-------------|------|
| oclaw2026linux | 100.111.79.93 | VM (server) |
| desis-macbook-air | 100.85.14.32 | Admin (client) |
| chromeos-nissa | 100.124.62.63 | Exit node |
| iphone172 | 100.89.118.36 | Blocked from oclaw |

## Gotchas

- **chromeos-nissa must be powered on and awake** for residential egress. If it sleeps, the watchdog fails over to Azure egress (~4 min window)
- **`tailscale ping` doesn't work when exit node is sleeping** — returns "timed out" with rc=0 and "no reply". Ping works fine when device is awake
- **Gateway `tailscale.mode` is unrelated** — keep it `"off"` in `openclaw.json`. Do not confuse with SSH/egress Tailscale usage
- **Exit node breaks Azure IMDS** — Tailscale routes `169.254.169.254` through the exit node tunnel. An ip rule exception (`priority 100, lookup main`) is needed to keep IMDS on `eth0`. Without this, the Foundry MI proxy can't get tokens and all LLM calls fail with 500. See [opslog](2026-02-20-tailscale-exit-node-breaks-imds.md)
- **Do NOT advertise oclaw as an exit node** — `tailscale set --advertise-exit-node` requires clearing `--exit-node` first (Tailscale can't use and be an exit node simultaneously). This drops chromeos-nissa residential egress and exposes the VM to 403 blocks. The VM should only **use** an exit node, never **be** one

## Files Modified

- `~/.ssh/config` (Mac) — `oclaw` points to Tailscale IP
- `CLAUDE.md` — Tailscale section added, NSG marked fallback-only, startup simplified
- `manage-oclaw/turn_on_oclaw_vm.md` — NSG step removed
- `manage-oclaw/plan-turn-on-tailscale.md` — full plan with all steps

## Files Created (on VM)

- `~/.openclaw/workspace/ops/watchdog/tailscale_egress_watchdog.py`
- `~/.openclaw/workspace/ops/watchdog/run_tailscale_egress_watchdog.sh`
- `~/.local/state/openclaw/tailscale-egress-watchdog.state`
