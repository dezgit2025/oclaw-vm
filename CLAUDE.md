# openclaw_vm Project Instructions

## Project Overview

Management tools, scripts, and documentation for the **oclaw** Azure VM infrastructure. This includes SSH tunnel management, NSG configuration, Docker services (draw.io, Foundry GPT52), and Google Drive OAuth integration.

## Azure Infrastructure

| Resource | Value |
|----------|-------|
| Resource Group | `RG_OCLAW2026` |
| Linux VM | `oclaw2026linux` (Standard_D4s_v3 — 4 vCPU / 16 GiB) |
| Windows VM | `oclaw-admin-win11m` |
| VM NSG | `oclaw2026linux-nsg` |
| Subnet NSG | `vnet-eastus2-snet-eastus2-1-nsg-eastus2` |
| Region | East US 2 |
| SSH Host | `oclaw` (defined in `~/.ssh/config`, uses Tailscale IP) |
| SSH User | `desazure` |
| SSH Key | `~/.ssh/oclaw-key-v4.pem` |
| VM Public IP | `20.81.190.88` (fallback only — use `oclaw-public` SSH alias) |
| VM Tailscale IP | `100.111.79.93` (primary — used by `oclaw` SSH alias) |

## Key Directories

| Path | Purpose |
|------|---------|
| `manage-oclaw/` | SSH tunnel manager, NSG setup script, OAuth docs |
| `manage-oclaw/opslog/` | Operational incident logs and breaking-change fixes |
| `docker/` | Docker-related configs |
| `venv/` | Local Python virtual environment |

## manage-oclaw/ Scripts

These are the primary operational scripts. See `manage-oclaw/README.md` for full docs.

| Script | Purpose | Usage |
|--------|---------|-------|
| `check-setup-nsg-for-oclaw-ssh.py` | Detects public IP, creates/updates NSG rules on both subnet + VM NSGs, tests SSH | **Fallback only** — not needed with Tailscale |
| `create-manage-tunnel-oclaw.py` | Manages SSH tunnel (ports 18792-18797) | `start` / `stop` / `restart` / `status` |

### Typical Workflow

```bash
cd manage-oclaw/
./create-manage-tunnel-oclaw.py start  # start tunnel (SSH goes over Tailscale — no NSG step)
```

## SSH Tunnel Ports

| Port | Service |
|------|---------|
| 18792 | openclaw-gateway |
| 18793 | gdrive auth/services |
| 18794 | Google OAuth redirect (Drive) |
| 18795 | Google OAuth redirect (Docs) |
| 18796 | Google OAuth redirect (Sheets) |
| 18797 | Google OAuth redirect (Calendar) |

## VM Paths (on oclaw2026linux)

| Path | Purpose |
|------|---------|
| `~/.config/openclaw-gdrive/credentials.json` | Google OAuth client secret |
| `~/.config/openclaw-gdrive/token-openclawshared.json` | Google Drive OAuth token (access + refresh) |
| `~/.config/openclaw-gdrive/token-docs-openclawshared.json` | Google Docs + Drive readonly OAuth token |
| `~/.openclaw/workspace/.venv-gmail/` | Python venv with google-auth-oauthlib |
| `~/.openclaw/workspace/skills/gdrive-openclawshared/scripts/auth.py` | OAuth auth script |
| `~/.openclaw/workspace/run-gdrive-auth.sh` | Shortcut to run the auth script |

## Tailscale

SSH to the VM uses Tailscale (WireGuard mesh) instead of the public IP. This eliminates the need for NSG rule management — Tailscale uses outbound-only connections, so no inbound firewall rules are required. Tailscale reconnects automatically after VM restart.

| Component | Value |
|-----------|-------|
| VM Tailscale IP | `100.111.79.93` |
| Mac Tailscale IP | `100.85.14.32` |
| Exit node | `chromeos-nissa` (`100.124.62.63`) — residential IP egress |
| SSH alias | `oclaw` → Tailscale IP; `oclaw-public` → public IP (fallback) |
| Tailscale version (VM) | 1.94.2 |

### Tailscale ACLs

Managed at https://login.tailscale.com/admin/acls. Current policy:

| Source | Destination | Allowed |
|--------|-------------|---------|
| MacBook | oclaw | Yes — all ports (SSH, admin) |
| oclaw | chromeos-nissa | Yes — exit node handshake |
| MacBook / oclaw | Internet (via exit node) | Yes |
| oclaw | MacBook | **Blocked** — deny by default |
| iPhone | oclaw | **Blocked** — deny by default |

### Exit Node (Residential IP Egress)

The VM routes internet traffic through `chromeos-nissa` (Android/ChromeOS) to egress from a residential IP (`108.29.69.37`). This avoids 403 blocks that many services apply to Azure datacenter IPs.

**Failover watchdog** runs every 2 min via cron:
- Checks if exit node is reachable (`tailscale ping`)
- After 2 consecutive failures → clears exit node (falls back to Azure native egress)
- When exit node recovers → re-enables residential egress
- Script: `~/.openclaw/workspace/ops/watchdog/tailscale_egress_watchdog.py`
- State: `~/.local/state/openclaw/tailscale-egress-watchdog.state`
- Logs: `~/.openclaw/logs/tailscale-egress-watchdog/YYYY-MM-DD.log`

**Quick checks:**

```bash
# Current egress IP
ssh oclaw "curl -s ifconfig.me"

# Watchdog state
ssh oclaw "cat ~/.local/state/openclaw/tailscale-egress-watchdog.state"

# Tailscale status
ssh oclaw "tailscale status"
```

**Important:** The chromeos-nissa exit node must be powered on and awake. If it sleeps, the watchdog will fail over to Azure egress automatically.

### IMDS Route Exception

The exit node routes all traffic — including Azure IMDS (`169.254.169.254`). An ip rule exception forces IMDS through `eth0`:

```bash
sudo ip rule add to 169.254.169.254 lookup main priority 100
```

This is persisted via `/etc/networkd-dispatcher/routable.d/50-imds-route.sh`. **Without this, the Foundry MI proxy cannot get tokens and all LLM calls fail with 500.** See [opslog](manage-oclaw/opslog/2026-02-20-tailscale-exit-node-breaks-imds.md).

### Gateway Tailscale Mode

The openclaw gateway has its own `tailscale.mode` setting in `~/.openclaw/openclaw.json`. This is a **separate concern** from SSH-over-Tailscale and exit node routing. Keep it set to `"mode": "off", "resetOnExit": false`. See [opslog](manage-oclaw/opslog/2026-02-20-gateway-crash-tailscale-mode-invalid.md) for what happens if it gets changed.

## NSG Rules (Fallback Only)

**Not needed for normal operations** — Tailscale bypasses NSG entirely.

Only run the NSG script if Tailscale is down and you need emergency SSH via the public IP:

```bash
./manage-oclaw/check-setup-nsg-for-oclaw-ssh.py    # creates AllowSSH-MyIP rules
ssh oclaw-public "hostname"                          # uses public IP alias
```

- Rule name: `AllowSSH-MyIP` (priority 100)
- Applied to both subnet NSG and VM NSG
- NSG rules get cleared on VM deallocation

## VM Auto-Shutdown & Startup

The VM auto-shuts down at ~11 PM nightly. When the user says "turn on oclaw VM" or similar, follow the steps in **[manage-oclaw/turn_on_oclaw_vm.md](manage-oclaw/turn_on_oclaw_vm.md)**.

**Quick reference** (Azure CLI is installed, `az login` already done):

1. `az vm start --name oclaw2026linux --resource-group RG_OCLAW2026`
2. `./manage-oclaw/create-manage-tunnel-oclaw.py start`

No NSG step — Tailscale reconnects automatically on boot.

## Check oclaw Gateway

The gateway is monitored by a lightweight watchdog cron job (no LLM). Full details: **[manage-oclaw/check_clawbot_gateway_test_ping_every_5_min_cron_.md](manage-oclaw/check_clawbot_gateway_test_ping_every_5_min_cron_.md)**

**Quick checks:**

```bash
# Gateway status
ssh oclaw "systemctl --user status openclaw-gateway.service --no-pager"

# Watchdog logs (today)
ssh oclaw "cat ~/.openclaw/logs/gateway-watchdog/$(date -u +%Y-%m-%d).log"

# Watchdog state (fail count + last restart)
ssh oclaw "cat ~/.local/state/openclaw/gateway-watchdog.state"
```

**How it works:** Cron runs every 5 min → checks systemd unit + TCP port 18789 → restarts after 2 consecutive failures (rate-limited to once per 30 min) → logs to `~/.openclaw/logs/gateway-watchdog/`.

**Restart gateway manually:**

```bash
ssh oclaw "python3 /home/desazure/.openclaw/workspace/ops/watchdog/restart_gateway.py"
```

This script restarts `openclaw-gateway.service` via systemd (user unit), logs timestamps, and confirms the service is active after restart.

## Google OAuth Reauth

**Trigger:** When user says "reauth google", "google reauth", "refresh google tokens", or similar.

**Prerequisites:** VM must be running and tunnel connected (port 18793 needed).

**Run from laptop:**

```bash
echo "Y" | ./google-reauth/laptop_google_reauth.sh oclaw assistantdesi@gmail.com
```

This calls the VM-side script at `/home/desazure/.openclaw/workspace/ops/google-auth/google_reauth.sh` which re-auths **all 6 Google services** in one shot:

| Service | Token Path (on VM) |
|---------|--------------------|
| Gmail | `~/.config/openclaw-gmail/token-assistantdesi_gmail_com.json` |
| GDrive | `~/.config/openclaw-gdrive/token-openclawshared.json` |
| GDocs | `~/.config/openclaw-gdrive/token-docs-openclawshared.json` |
| GSheets | `~/.config/openclaw-gdrive/token-sheets-openclawshared.json` |
| GCal (read) | `~/.config/openclaw-gcal/token-readonly.json` |
| GCal (write) | `~/.config/openclaw-gcal/token-write.json` |

**After reauth**, optionally run the audit:
```bash
ssh oclaw "python3 /home/desazure/.openclaw/workspace/ops/google-auth/audit_google_oauth.py"
```

## Known Patches on VM (will be lost on npm update)

The openclaw dist on the VM has been patched in-place. These patches are overwritten if `npm update -g openclaw` is run. Check `manage-oclaw/opslog/` for full details.

| Patch | Date | Files (on VM under `~/.npm-global/lib/node_modules/openclaw/dist/`) | Opslog |
|-------|------|------|--------|
| Add `pollIntervalMs` to telegram Zod schema | 2026-02-20 | `config-BEpchvJh.js`, `config-BseT0AMx.js`, `config-CQx0LPGX.js`, `config-F0Q6PyfW.js` | [opslog](manage-oclaw/opslog/2026-02-20-fix-telegram-pollIntervalMs-schema.md) |

**Note:** v2026.2.17 added `pollIntervalMs` to an internal schema (`z.number().int().nonnegative().optional()` at one level) but the `.strict()` telegram channel config schema still rejects it. The patch is still required. A non-fatal "Unrecognized key" warning from the pre-validation check still appears in logs but does not prevent startup.

**After any openclaw update**, re-apply the patch: add `pollIntervalMs: z.number().int().positive().optional(),` after the `streamMode` enum block in each `config-*.js` file (search for `.default("partial"),` — unique to telegram schema).

Current telegram config includes `"pollIntervalMs": 10000` (10 seconds).

## Foundry Proxy Fix

The Foundry MI proxy (`server.mjs`) strips `foundry/` prefix from model names before forwarding to Azure. The monitor cron job uses a static script instead of LLM-generated bash. Full details: **[manage-oclaw/fix-foundry-model-proxy.md](manage-oclaw/fix-foundry-model-proxy.md)**

## Starbucks WiFi Ops (Rate-Limit Bypass)

Docs and test results for bypassing Starbucks WiFi traffic shaping when working remotely. Full findings: **[starbucks_ops/rate-limit-bypass/findings-2026-02-19.md](starbucks_ops/rate-limit-bypass/findings-2026-02-19.md)**

**Key findings (2026-02-19):**
- Starbucks shapes **per-device (MAC address)** — ~15 Mbps cap per device to Azure
- Not per-port, per-protocol, or per-flow — tested SSH on ports 22/443/993/123, WireGuard UDP, ByeDPI packet manipulation
- Multiple parallel streams make it worse (4 streams = 6.7 Mbps vs 1 stream = 15 Mbps)
- VM itself has ~408 Mbps to Cloudflare — bottleneck is entirely the WiFi link

**Viable bypass: Multi-device bonding**
- Add a second device with different MAC → gets its own ~15 Mbps session
- **Android USB tether** passes WiFi through (iOS does NOT — only shares cellular)
- **GL.iNet travel router** ($30-70) with spoofed MAC + USB-C Ethernet to Mac
- Bond interfaces with `dispatch-proxy` (npm) → SOCKS proxy round-robins across links
- USB WiFi adapters do NOT work on Apple Silicon (no kernel extension support)

**TODO:** Test Android WiFi tethering + bonding at Starbucks

## Sensitive Files (do not commit)

- `credentials.json` -- Google OAuth client secret
- `token.json` -- Azure/Google tokens
- `.env.*` files (non-example ones)
- `~/.ssh/oclaw-key-v4.pem`
