# Managing oclaw VM with VS Code

## Setup

1. Install the **Remote - SSH** extension in VS Code
2. Press `Cmd+Shift+P` → **Remote-SSH: Connect to Host...**
3. Type `oclaw` — it reads your `~/.ssh/config` automatically:
   ```
   Host oclaw
     HostName 20.81.190.88
     User desazure
     IdentityFile ~/.ssh/oclaw-key-v4.pem
   ```
4. VS Code opens a remote window connected to the VM

## What You Can Do

- Browse and edit files on the VM directly
- Open integrated terminal (runs on the VM)
- Install extensions that run remotely (Python, linters, etc.)
- Use the file explorer to navigate VM directories
- Run and debug scripts on the VM

## Useful Paths to Open

| Path | Contents |
|------|----------|
| `~/.openclaw/workspace/` | Main workspace (skills, scripts, venvs) |
| `~/.config/openclaw-gdrive/` | Google OAuth credentials and tokens |
| `~/.config/openclaw-gcal/` | Google Calendar OAuth credentials and tokens |

## Prerequisites

- VM must be running (`az vm start --name oclaw2026linux --resource-group RG_OCLAW2026`)
- NSG rules must allow SSH from your IP (run `./check-setup-nsg-for-oclaw-ssh.py`)
- VS Code uses its own SSH connection — the port tunnel (18792-18797) is **not required** for VS Code, only for forwarding services to localhost

## Port Forwarding in VS Code

VS Code Remote-SSH can also forward ports. If you prefer VS Code over the tunnel script:

1. Connect to `oclaw` via Remote-SSH
2. Open the **Ports** tab in the bottom panel
3. Click **Forward a Port** and enter `18792` (or any port)
4. Access it at `localhost:18792` in your browser

This is an alternative to using `create-manage-tunnel-oclaw.py` but both work fine.
