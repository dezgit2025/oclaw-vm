# Google OAuth Reauth — oclaw VM

Full workflow for reauthorizing Google services on the oclaw VM.

---

## Prerequisites

Ensure the SSH tunnel is running on your Mac (all OAuth ports are included by default):

```bash
cd ~/Projects/openclaw_vm
./manage-oclaw/create-manage-tunnel-oclaw.py start
```

---

## Per-Service Reauth Scripts

Each script runs **directly on the VM**. SSH in first, then run the script.

```bash
ssh oclaw
```

| Service | Script | Port | Token |
|---------|--------|------|-------|
| Gmail | `reauth-gmail.sh` | 18793 | `~/.config/openclaw-gmail/token-assistantdesi_gmail_com.json` |
| Google Drive | `reauth-drive.sh` | 18794 | `~/.config/openclaw-gdrive/token-openclawshared.json` |
| Google Docs | `reauth-docs.sh` | 18795 | `~/.config/openclaw-gdrive/token-docs-openclawshared.json` |
| Google Sheets | `reauth-sheets.sh` | 18796 | `~/.config/openclaw-gdrive/token-sheets-openclawshared.json` |
| Google Calendar (write) | `reauth-gcal-write.sh` | 18797 | `~/.config/openclaw-gcal/token-write.json` |
| Google Calendar (readonly) | `reauth-gcal-readonly.sh` | 18798 | `~/.config/openclaw-gcal/token-readonly.json` |

All scripts live on the VM at:
```
~/.openclaw/workspace/ops/google-auth/
```

### Run commands (on oclaw)

```bash
# Gmail
~/.openclaw/workspace/ops/google-auth/reauth-gmail.sh

# Google Drive
~/.openclaw/workspace/ops/google-auth/reauth-drive.sh

# Google Docs
~/.openclaw/workspace/ops/google-auth/reauth-docs.sh

# Google Sheets
~/.openclaw/workspace/ops/google-auth/reauth-sheets.sh

# Google Calendar (write)
~/.openclaw/workspace/ops/google-auth/reauth-gcal-write.sh

# Google Calendar (readonly)
~/.openclaw/workspace/ops/google-auth/reauth-gcal-readonly.sh
```

Each script:
1. Kills stale processes on its OAuth port
2. Deletes the existing token (prevents `invalid_grant` errors)
3. Runs the OAuth flow and prints a Google URL
4. Open the URL in your **Mac browser** and approve

---

## Full Reauth (all 6 services at once)

Run from Mac:

```bash
echo "Y" | ./google-reauth/laptop_google_reauth.sh oclaw assistantdesi@gmail.com
```

To nuke all tokens first:

```bash
ssh oclaw "rm -f ~/.config/openclaw-gmail/token-*.json \
  ~/.config/openclaw-gdrive/token-*.json \
  ~/.config/openclaw-gcal/token-*.json"
```

---

## Troubleshooting

**`invalid_grant: Token has been expired or revoked`** — the per-service scripts delete the token automatically. If running auth.py directly, delete the token manually first:

```bash
# Example for Drive
ssh oclaw "rm -f ~/.config/openclaw-gdrive/token-openclawshared.json"
```

**"Address already in use"** — kill the port:

```bash
ssh oclaw "sudo fuser -k <port>/tcp"
```

---

## Verify After Reauth

```bash
ssh oclaw "python3 /home/desazure/.openclaw/workspace/ops/google-auth/audit_google_oauth.py"
```

---

## Script Maintenance Notes

**Source files (Mac):** `google-reauth/reauth-*.sh`
**Deployed (VM):** `~/.openclaw/workspace/ops/google-auth/reauth-*.sh`

**IMPORTANT — Script design rule:** Scripts must run **directly on the VM** with no inner `ssh oclaw` calls. If given a script that contains `ssh oclaw`, strip those calls so auth.py runs locally. Then deploy:

```bash
scp google-reauth/reauth-<service>.sh oclaw:/home/desazure/.openclaw/workspace/ops/google-auth/reauth-<service>.sh
ssh oclaw "chmod +x /home/desazure/.openclaw/workspace/ops/google-auth/reauth-<service>.sh"
```
