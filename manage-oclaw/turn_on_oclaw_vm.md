# Turn On oclaw VM

The VM auto-shuts down at ~11 PM nightly. Run these steps each morning or whenever you need it back.

## Prerequisites (already done)

- Azure CLI installed (`az`)
- `az login` already completed
- SSH config for `oclaw` in `~/.ssh/config`

## Steps

### 1. Start the VM

```bash
az vm start --name oclaw2026linux --resource-group RG_OCLAW2026
```

### 2. Setup NSG Rules for SSH

NSG rules get cleared when the VM deallocates. This re-creates them for your current IP.

```bash
./manage-oclaw/check-setup-nsg-for-oclaw-ssh.py
```

### 3. Start the SSH Tunnel

```bash
./manage-oclaw/create-manage-tunnel-oclaw.py start
```

### 4. Verify

```bash
./manage-oclaw/create-manage-tunnel-oclaw.py status
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18792/
```

## One-Liner

```bash
az vm start --name oclaw2026linux --resource-group RG_OCLAW2026 && ./manage-oclaw/check-setup-nsg-for-oclaw-ssh.py && ./manage-oclaw/create-manage-tunnel-oclaw.py start
```

## What This Does

1. **Starts the VM** -- brings it out of deallocated state
2. **NSG rules** -- detects your public IP, creates `AllowSSH-MyIP` rules on both subnet and VM NSGs (priority 100), tests SSH
3. **Tunnel** -- forwards ports 18792, 18793, 18794 from the VM to localhost

## Notes

- If your IP changes mid-day (VPN, network switch), just re-run step 2
- The tunnel script is idempotent -- running `start` when already running does nothing
- See `manage-oclaw/README.md` for full script documentation
