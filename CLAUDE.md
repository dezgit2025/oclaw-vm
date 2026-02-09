# openclaw_vm Project Instructions

## Project Overview

Management tools, scripts, and documentation for the **oclaw** Azure VM infrastructure. This includes SSH tunnel management, NSG configuration, Docker services (draw.io, Foundry GPT52), and Google Drive OAuth integration.

## Azure Infrastructure

| Resource | Value |
|----------|-------|
| Resource Group | `RG_OCLAW2026` |
| Linux VM | `oclaw2026linux` |
| Windows VM | `oclaw-admin-win11m` |
| VM NSG | `oclaw2026linux-nsg` |
| Subnet NSG | `vnet-eastus2-snet-eastus2-1-nsg-eastus2` |
| Region | East US 2 |
| SSH Host | `oclaw` (defined in `~/.ssh/config`) |
| SSH User | `desazure` |
| SSH Key | `~/.ssh/oclaw-key-v4.pem` |
| VM IP | `20.81.190.88` |

## Key Directories

| Path | Purpose |
|------|---------|
| `manage-oclaw/` | SSH tunnel manager, NSG setup script, OAuth docs |
| `docker/` | Docker-related configs |
| `venv/` | Local Python virtual environment |

## manage-oclaw/ Scripts

These are the primary operational scripts. See `manage-oclaw/README.md` for full docs.

| Script | Purpose | Usage |
|--------|---------|-------|
| `check-setup-nsg-for-oclaw-ssh.py` | Detects public IP, creates/updates NSG rules on both subnet + VM NSGs, tests SSH | Run when IP changes or before connecting |
| `create-manage-tunnel-oclaw.py` | Manages SSH tunnel (ports 18792-18795) | `start` / `stop` / `restart` / `status` |

### Typical Workflow

```bash
cd manage-oclaw/
./check-setup-nsg-for-oclaw-ssh.py    # ensure NSG allows SSH from current IP
./create-manage-tunnel-oclaw.py start  # start tunnel in background
```

## SSH Tunnel Ports

| Port | Service |
|------|---------|
| 18792 | openclaw-gateway |
| 18793 | gdrive auth/services |
| 18794 | Google OAuth redirect (Drive) |
| 18795 | Google OAuth redirect (Docs) |

## VM Paths (on oclaw2026linux)

| Path | Purpose |
|------|---------|
| `~/.config/openclaw-gdrive/credentials.json` | Google OAuth client secret |
| `~/.config/openclaw-gdrive/token-openclawshared.json` | Google Drive OAuth token (access + refresh) |
| `~/.config/openclaw-gdrive/token-docs-openclawshared.json` | Google Docs + Drive readonly OAuth token |
| `~/.openclaw/workspace/.venv-gmail/` | Python venv with google-auth-oauthlib |
| `~/.openclaw/workspace/skills/gdrive-openclawshared/scripts/auth.py` | OAuth auth script |
| `~/.openclaw/workspace/run-gdrive-auth.sh` | Shortcut to run the auth script |

## NSG Rules

- Rule name: `AllowSSH-MyIP` (priority 100)
- Applied to both subnet NSG and VM NSG
- A JIT deny rule exists at priority 4096 -- our rule at 100 takes precedence
- NSG rules may be cleared when the VM is deallocated; re-run `check-setup-nsg-for-oclaw-ssh.py` after starting a deallocated VM

## VM Auto-Shutdown & Startup

The VM auto-shuts down at ~11 PM nightly. When the user says "turn on oclaw VM" or similar, follow the steps in **[manage-oclaw/turn_on_oclaw_vm.md](manage-oclaw/turn_on_oclaw_vm.md)**.

**Quick reference** (Azure CLI is installed, `az login` already done):

1. `az vm start --name oclaw2026linux --resource-group RG_OCLAW2026`
2. `./manage-oclaw/check-setup-nsg-for-oclaw-ssh.py` (NSG rules get cleared on deallocation)
3. `./manage-oclaw/create-manage-tunnel-oclaw.py start`

## Sensitive Files (do not commit)

- `credentials.json` -- Google OAuth client secret
- `token.json` -- Azure/Google tokens
- `.env.*` files (non-example ones)
- `~/.ssh/oclaw-key-v4.pem`
