# Plan: Replace NSG-based SSH with Tailscale + Residential Egress for oclaw VM

## Context

The Azure VM `oclaw2026linux` currently requires NSG rules to allow SSH (port 22) from the user's public IP. These rules get **cleared on every VM deallocation** and must be re-created via `check-setup-nsg-for-oclaw-ssh.py`. This is tedious and error-prone — especially since the VM auto-shuts down nightly.

Additionally, outbound requests from the VM get **403-blocked** by many services because Azure datacenter IPs are in well-known cloud ranges. Egressing through a residential IP solves this.

Tailscale creates a persistent WireGuard mesh between Mac and VM that bypasses NSG entirely (uses outbound connections only). The user already has Tailscale installed on their Mac with an active account.

## Three Goals

| # | Goal | What it does |
|---|------|-------------|
| 1 | **Tailscale for SSH** | Eliminate NSG script from daily workflow — SSH works after VM restart with zero manual steps |
| 2 | **Tailscale exit node** | Route VM internet traffic through home Linux machine's residential IP to avoid 403 blocks |
| 3 | **Gateway Tailscale mode** | Stays `"off"` — untouched, separate concern |

## Why NSG is no longer needed

| | Current (public IP SSH) | With Tailscale |
|--|--|--|
| **Connection path** | Inbound to port 22 on public IP | Outbound-only WireGuard mesh (UDP hole-punch or DERP relay) |
| **NSG rules needed?** | Yes — must allow inbound 22 from your IP | **No** — all connections are outbound from the VM, which Azure allows by default |
| **VM dealloc/restart** | NSG rules wiped → must re-run script | Tailscale reconnects automatically on boot (systemd service) |
| **IP changes** | Must re-run script to update NSG with new IP | Doesn't matter — Tailscale uses node identity, not IPs |

## Steps

### 1. Install Tailscale on the VM

```bash
# SSH in via current NSG method (one last time)
ssh oclaw

# Install
curl -fsSL https://tailscale.com/install.sh | sh

# Start + auth (prints a URL to open in browser)
sudo tailscale up

# Verify
tailscale ip -4          # note the 100.x.y.z IP
sudo systemctl enable tailscaled
sudo systemctl status tailscaled
```

### 2. Verify Tailscale connectivity from Mac

```bash
tailscale ping oclaw2026linux    # or ping 100.x.y.z
```

### 3. Update `~/.ssh/config`

Rename current entry to `oclaw-public` (fallback), add new `oclaw` pointing to Tailscale:

```
Host oclaw
  HostName 100.x.y.z              # Tailscale IP (replace with actual)
  User desazure
  IdentityFile ~/.ssh/oclaw-key-v4.pem

Host oclaw-public
  HostName 20.81.190.88            # Original public IP (emergency fallback)
  User desazure
  IdentityFile ~/.ssh/oclaw-key-v4.pem
```

### 4. Configure home Linux as exit node

On the home Linux machine:

```bash
# Enable IP forwarding (required for exit node)
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf

# Advertise as exit node
sudo tailscale up --advertise-exit-node
```

Then approve the exit node in the **Tailscale admin console** (https://login.tailscale.com/admin/machines).

### 5. Set VM to use home Linux as exit node

```bash
ssh oclaw "sudo tailscale set --exit-node=<home-machine-tailscale-hostname>"
```

Verify egress IP changed:

```bash
ssh oclaw "curl -s ifconfig.me"   # should show home residential IP, not Azure IP
```

### 6. Deploy exit node failover watchdog

**Purpose:** If the home exit node goes down, automatically fall back to Azure native egress. When it recovers, re-enable residential egress.

```
┌─────────────────────────────────────┐
│  Cron (every 2 min)                 │
│                                     │
│  tailscale ping home-linux          │
│     │                               │
│     ├─ reachable → set exit node    │
│     │              (residential IP) │
│     │                               │
│     └─ unreachable → clear exit     │
│                node (Azure egress)  │
└─────────────────────────────────────┘
```

| State | Exit node | Egress path | Trigger |
|-------|-----------|-------------|---------|
| Normal | Home Linux | Residential IP | Watchdog confirms ping OK |
| Home down | Cleared | Azure native | Watchdog detects 2 consecutive ping failures |
| Home recovers | Re-set | Residential IP | Watchdog detects ping OK again |

**Script location on VM:** `~/.openclaw/workspace/ops/watchdog/tailscale_egress_watchdog.py`
**State file:** `~/.local/state/openclaw/tailscale-egress-watchdog.state`
**Logs:** `~/.openclaw/logs/tailscale-egress-watchdog/YYYY-MM-DD.log`
**Cron:** Every 2 minutes

**Failover window:** Worst case ~4 minutes (2 cron cycles with 2 consecutive failures required).

### 7. Validate everything works

- `ssh oclaw "echo OK && hostname"` — SSH over Tailscale
- `./manage-oclaw/create-manage-tunnel-oclaw.py start && status` — tunnel still works
- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18792/` — gateway reachable
- `ssh oclaw "curl -s ifconfig.me"` — shows residential IP (exit node active)
- `ssh oclaw "systemctl --user status openclaw-gateway.service --no-pager"` — gateway healthy

### 8. Update documentation

**Files to update:**

| File | Change |
|------|--------|
| `CLAUDE.md` | Add Tailscale section (SSH IP, exit node, watchdog), update SSH Host info, simplify startup workflow (remove NSG step), mark NSG script as fallback-only |
| `manage-oclaw/turn_on_oclaw_vm.md` | Remove NSG step — startup becomes: `az vm start` → `tunnel start` (2 steps instead of 3) |

**Files to keep unchanged (fallback):**
- `check-setup-nsg-for-oclaw-ssh.py` — emergency use if Tailscale is down
- `enable-ssh-oclaw.sh`, `fix-oclaw-linux-nsg.sh` — same

### 9. Log to opslog

Create `manage-oclaw/opslog/2026-02-XX-tailscale-ssh-and-egress.md`

## What does NOT change

- All `ssh oclaw` commands — alias still resolves
- `create-manage-tunnel-oclaw.py` — same SSH tunnel, different transport
- Google OAuth redirect URIs (`http://127.0.0.1:18794-18797`) — tunnel still forwards to localhost
- Gateway's `"tailscale": {"mode": "off"}` config — untouched, separate concern
- NSG deny rules for ports 18789/18791 — kept for defense in depth
- SSH key auth — same key, same user

## New startup workflow

```bash
az vm start --name oclaw2026linux --resource-group RG_OCLAW2026
./manage-oclaw/create-manage-tunnel-oclaw.py start
# That's it — no NSG step. Tailscale reconnects on boot. Exit node watchdog handles egress.
```

## Verification

1. SSH over Tailscale: `ssh oclaw "hostname"`
2. Tunnel ports: `curl http://127.0.0.1:18792/`
3. Egress IP: `ssh oclaw "curl -s ifconfig.me"` → residential IP
4. VM dealloc/restart cycle: deallocate → start → verify SSH works without running NSG script
5. Exit node failover: stop home machine → verify VM falls back to Azure egress → restart home → verify residential egress resumes
6. Fallback: `ssh oclaw-public` still works (after manually running NSG script if needed)
