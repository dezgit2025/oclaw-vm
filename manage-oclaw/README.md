# manage-oclaw: SSH Tunnel & NSG Manager for oclaw VM

Manages a persistent SSH tunnel to the **oclaw** Azure VM, forwarding ports `18792`-`18795` from the remote host to your local machine. Includes a companion script to auto-configure Azure NSG rules for SSH access and a helper script on the VM for Google OAuth authentication.

## Prerequisites

- Python 3
- Azure CLI (`az`) logged in with permissions to manage NSG rules in `RG_OCLAW2026`
- SSH config entry for `oclaw` in `~/.ssh/config`:

```
Host oclaw
  HostName 20.81.190.88
  User desazure
  IdentityFile ~/.ssh/oclaw-key-v4.pem
```

- The SSH key `~/.ssh/oclaw-key-v4.pem` must exist with correct permissions (`chmod 600`)

## Quick Start

```bash
cd manage-oclaw/

# 1. Ensure NSG rules allow SSH from your current IP
./check-setup-nsg-for-oclaw-ssh.py

# 2. Start the tunnel
./create-manage-tunnel-oclaw.py start
```

## Scripts

### `check-setup-nsg-for-oclaw-ssh.py` -- NSG Setup & Verification

Ensures your current public IP has SSH access through both the subnet and VM NSGs.

```bash
./check-setup-nsg-for-oclaw-ssh.py
```

**What it does (in order):**

1. Detects your current public IP (via `ifconfig.me`)
2. Verifies the VM (`oclaw2026linux`) is running
3. Checks both NSGs for an `AllowSSH-MyIP` rule:
   - **Subnet NSG**: `vnet-eastus2-snet-eastus2-1-nsg-eastus2`
   - **VM NSG**: `oclaw2026linux-nsg`
4. Creates the rule if missing, or updates it if your IP has changed
5. Tests SSH connectivity

Run this script whenever your IP changes (e.g., new network, VPN toggle, ISP change).

### `create-manage-tunnel-oclaw.py` -- Tunnel Manager

Manages the SSH tunnel that forwards ports `18792`-`18795`.

```bash
# Start tunnel in background (recommended default)
./create-manage-tunnel-oclaw.py start

# Check if tunnel is running
./create-manage-tunnel-oclaw.py status

# Stop the tunnel
./create-manage-tunnel-oclaw.py stop

# Restart (stop + start in background)
./create-manage-tunnel-oclaw.py restart

# Start tunnel in foreground (optional, blocks terminal)
./create-manage-tunnel-oclaw.py start -f
```

> **Default: background mode.** Use `start` (not `start -f`) for normal use. The tunnel detaches and your terminal stays free. Use `status` to check it anytime.

#### Commands

| Command | Description |
|---------|-------------|
| `start` | **(default)** Start tunnel in background. Exits immediately, tunnel runs detached. |
| `start -f` | Start tunnel in foreground. Blocks until you press Ctrl+C. Rarely needed. |
| `stop` | Stop a running tunnel (sends SIGTERM, then SIGKILL if needed). |
| `restart` | Stop then start the tunnel in background. |
| `status` | Show whether the tunnel is running and display connection details. |

## What the Tunnel Forwards

| Local | Remote (on oclaw VM) | Service |
|-------|----------------------|---------|
| `127.0.0.1:18792` | `127.0.0.1:18792` | openclaw-gateway |
| `127.0.0.1:18793` | `127.0.0.1:18793` | gdrive auth/services |
| `127.0.0.1:18794` | `127.0.0.1:18794` | Google OAuth redirect (Drive) |
| `127.0.0.1:18795` | `127.0.0.1:18795` | Google OAuth redirect (Docs) |

Equivalent manual command:
```bash
ssh -N -L 18792:127.0.0.1:18792 -L 18793:127.0.0.1:18793 -L 18794:127.0.0.1:18794 -L 18795:127.0.0.1:18795 oclaw
```

## Google Drive OAuth Setup

Authenticates the VM to access Google Drive (openclawshared) via OAuth.

### Prerequisites (one-time)

1. Get a Google OAuth **Desktop app** client JSON from Google Cloud Console
2. Copy it to the VM:
   ```bash
   scp ~/Downloads/credentials.json oclaw:/home/desazure/.config/openclaw-gdrive/credentials.json
   ```
   If the directory doesn't exist:
   ```bash
   ssh oclaw 'mkdir -p /home/desazure/.config/openclaw-gdrive'
   ```

### Running the Auth Flow

1. Make sure the SSH tunnel is running (port 18794 is needed for the OAuth redirect):
   ```bash
   ./create-manage-tunnel-oclaw.py start
   ```

2. SSH into the VM and run the auth script:
   ```bash
   ssh oclaw
   /home/desazure/.openclaw/workspace/run-gdrive-auth.sh
   ```

3. The script prints a Google auth URL. Open it in an **incognito browser window** and sign in with **desi4k@gmail.com**.

4. After approving, Google redirects to `http://127.0.0.1:18794/` which travels back through the SSH tunnel to the auth script on the VM.

5. On success you'll see: `OK: wrote token to ~/.config/openclaw-gdrive/token-openclawshared.json`

### Files on the VM

| File | Path | Purpose |
|------|------|---------|
| credentials.json | `~/.config/openclaw-gdrive/credentials.json` | Google OAuth client secret (Desktop app) |
| Drive token | `~/.config/openclaw-gdrive/token-openclawshared.json` | OAuth token for Google Drive (port 18794) |
| Docs token | `~/.config/openclaw-gdrive/token-docs-openclawshared.json` | OAuth token for Google Docs + Drive readonly (port 18795) |
| auth script | `~/.openclaw/workspace/skills/gdrive-openclawshared/scripts/auth.py` | Runs the OAuth flow |
| run helper | `~/.openclaw/workspace/run-gdrive-auth.sh` | Shortcut to run the Drive auth script |

### Token Refresh

The token auto-refreshes using the stored refresh token. You only need to re-run the auth flow if:
- The token file is deleted
- The refresh token is revoked in Google Account settings
- OAuth scopes change

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `Address already in use` (port 18794) | Kill the stale process: `ssh oclaw 'ss -tlnp \| grep 18794'` then `ssh oclaw 'kill <PID>'` |
| `Missing credentials.json` | Copy your Google OAuth client JSON to `~/.config/openclaw-gdrive/credentials.json` on the VM |
| `ModuleNotFoundError: google_auth_oauthlib` | Install: `/home/desazure/.openclaw/workspace/.venv-gmail/bin/pip install google-auth-oauthlib` |
| OAuth redirect fails / can't connect | Ensure tunnel is running with port 18794: `./create-manage-tunnel-oclaw.py status` |
| Wrong Google account | Use incognito window to avoid cached sessions |

See [gmail-oauth-token-flow-docs.md](gmail-oauth-token-flow-docs.md) for a detailed explanation of how the OAuth flow works.

## How It Works

1. **PID tracking** -- On start, the tunnel script spawns the SSH process and writes its PID to `.tunnel-oclaw.pid`. This file is used by `status`, `stop`, and `restart` to find the running process.

2. **Duplicate prevention** -- Before starting, the script checks if a tunnel is already running (via the PID file + process check). If it is, it prints a message and exits without starting a second one.

3. **Clean shutdown** -- `stop` sends SIGTERM to the SSH process, waits 1 second, and sends SIGKILL if it's still alive. The PID file is removed after shutdown.

4. **Foreground mode** -- With `-f`, the script blocks and waits for the SSH process. It installs signal handlers for SIGINT (Ctrl+C) and SIGTERM to clean up the PID file and terminate SSH gracefully.

5. **Stale PID cleanup** -- If the PID file exists but the process is dead (e.g., after a reboot), the script removes the stale PID file and treats the tunnel as not running.

6. **NSG auto-config** -- The NSG script creates rules named `AllowSSH-MyIP` at priority 100 (above the JIT deny rule at 4096). If the rule already exists with a stale IP, it updates in place rather than creating a duplicate.

## Keeping the Tunnel Persistent

### Option 1: Manual (ad hoc use)

Start the tunnel when you need it and stop it when done:

```bash
./create-manage-tunnel-oclaw.py start
# ... do work ...
./create-manage-tunnel-oclaw.py stop
```

### Option 2: Launch Agent (auto-start on login)

Create a macOS Launch Agent to start the tunnel automatically on login and restart it if it dies.

1. Create the plist file:

```bash
cat > ~/Library/LaunchAgents/com.oclaw.tunnel.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.oclaw.tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/dez/Projects/openclaw_vm/manage-oclaw/create-manage-tunnel-oclaw.py</string>
        <string>start</string>
        <string>-f</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/oclaw-tunnel.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/oclaw-tunnel.err</string>
</dict>
</plist>
EOF
```

2. Load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.oclaw.tunnel.plist
```

3. Manage it:

```bash
# Check status
launchctl list | grep oclaw

# Stop
launchctl unload ~/Library/LaunchAgents/com.oclaw.tunnel.plist

# View logs
tail -f /tmp/oclaw-tunnel.log
tail -f /tmp/oclaw-tunnel.err
```

### Option 3: Cron-based health check

Add a cron job that checks and restarts the tunnel every 5 minutes:

```bash
crontab -e
```

Add this line:

```
*/5 * * * * /Users/dez/Projects/openclaw_vm/manage-oclaw/create-manage-tunnel-oclaw.py start 2>&1 | logger -t oclaw-tunnel
```

The `start` command is idempotent -- if the tunnel is already running, it does nothing.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Tunnel failed to start` | Run `./check-setup-nsg-for-oclaw-ssh.py` to verify NSG + SSH |
| Stale PID file after reboot | Run `status` or `start` -- it auto-cleans stale PIDs |
| Port already in use | Check what's using it: `lsof -i :18792 -i :18793 -i :18794 -i :18795` |
| SSH key permission denied | `chmod 600 ~/.ssh/oclaw-key-v4.pem` |
| VM unreachable | Run `./check-setup-nsg-for-oclaw-ssh.py` -- your IP may have changed |
| NSG rule exists but wrong IP | The NSG script auto-detects and updates stale IPs |

## Files

| File | Purpose |
|------|---------|
| `create-manage-tunnel-oclaw.py` | Tunnel manager -- start/stop/restart/status for SSH tunnel |
| `check-setup-nsg-for-oclaw-ssh.py` | NSG setup -- detects IP, creates/updates NSG rules, tests SSH |
| `gmail-oauth-token-flow-docs.md` | Detailed explanation of the Google OAuth flow with diagrams |
| `.tunnel-oclaw.pid` | Auto-generated PID file for tracking the running tunnel process |
