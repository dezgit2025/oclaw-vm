# Turn On oclaw VM

The VM auto-shuts down at ~11 PM nightly. Run these steps each morning or whenever you need it back.

## Prerequisites (already done)

- Azure CLI installed (`az`)
- `az login` already completed
- SSH config for `oclaw` in `~/.ssh/config` (points to Tailscale IP `100.111.79.93`)
- Tailscale running on Mac and VM

## Steps

### 1. Start the VM

```bash
az vm start --name oclaw2026linux --resource-group RG_OCLAW2026
```

### 2. Start the SSH Tunnel

```bash
./manage-oclaw/create-manage-tunnel-oclaw.py start
```

That's it — Tailscale reconnects automatically on boot. No NSG step needed.

### 3. Verify

```bash
./manage-oclaw/create-manage-tunnel-oclaw.py status
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18792/
```

## One-Liner

```bash
az vm start --name oclaw2026linux --resource-group RG_OCLAW2026 && ./manage-oclaw/create-manage-tunnel-oclaw.py start
```

## What This Does

1. **Starts the VM** -- brings it out of deallocated state; Tailscale auto-reconnects
2. **Tunnel** -- forwards ports 18792-18797 from the VM to localhost via SSH over Tailscale

## Egress via Exit Node

The VM egresses internet traffic through `chromeos-nissa` (Tailscale exit node) using a residential IP to avoid 403 blocks from cloud IP ranges. A watchdog cron (every 2 min) auto-fails over to Azure native egress if the exit node goes down, and restores residential egress when it recovers.

## Fallback: NSG-Based SSH

If Tailscale is down and you need emergency access via the public IP:

```bash
./manage-oclaw/check-setup-nsg-for-oclaw-ssh.py    # re-create NSG rules
ssh oclaw-public "hostname"                          # uses public IP alias
```

## Notes

- The tunnel script is idempotent -- running `start` when already running does nothing
- See `manage-oclaw/README.md` for full script documentation
