# Google OAuth Reauth Instructions (oclaw VM)

Reauthorize all Google services on the oclaw VM. Run from your **Mac**.

## Step 1: Open SSH Tunnel (Mac Terminal 1)

Open a terminal on your Mac and run:

```bash
ssh -N -L 18793:127.0.0.1:18793 -L 18794:127.0.0.1:18794 -L 18795:127.0.0.1:18795 -L 18796:127.0.0.1:18796 -L 18797:127.0.0.1:18797 -L 18798:127.0.0.1:18798 oclaw
```

Leave it running (no output is normal).

## Step 2: SSH into the VM (Mac Terminal 2)

```bash
ssh -t oclaw
```

## Step 3: Clear Ports on the VM

Kill anything holding the OAuth ports:

```bash
sudo fuser -k 18793/tcp 18794/tcp 18795/tcp 18796/tcp 18797/tcp 18798/tcp
```

## Step 4: Delete Stale Tokens (if refresh fails)

```bash
rm -f ~/.config/openclaw-gmail/token-*.json
rm -f ~/.config/openclaw-gdrive/token-*.json
rm -f ~/.config/openclaw-gcal/token-*.json
```

## Step 5: Run Each Service (one at a time)

Each command prints a Google URL. Open it in your Mac browser and approve. Wait for "OK" before moving to the next.

### 1. Gmail

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  /home/desazure/.openclaw/workspace/skills/gmail-drafts/scripts/auth.py \
  --account assistantdesi@gmail.com \
  --port 18793
```

### 2. Google Drive

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  /home/desazure/.openclaw/workspace/skills/gdrive-openclawshared/scripts/auth.py \
  --account assistantdesi@gmail.com \
  --token ~/.config/openclaw-gdrive/token-openclawshared.json \
  --port 18794
```

### 3. Google Docs

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  /home/desazure/.openclaw/workspace/skills/gdocs-openclawshared/scripts/auth_docs.py \
  --account assistantdesi@gmail.com \
  --token ~/.config/openclaw-gdrive/token-docs-openclawshared.json \
  --port 18795
```

### 4. Google Sheets

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  /home/desazure/.openclaw/workspace/skills/gsheets-openclawshared/scripts/auth_sheets.py \
  --account assistantdesi@gmail.com \
  --token ~/.config/openclaw-gdrive/token-sheets-openclawshared.json \
  --port 18796
```

### 5. Google Calendar (write)

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  /home/desazure/.openclaw/workspace/skills/gcal-openclaw/scripts/auth_write.py \
  --account assistantdesi@gmail.com \
  --token ~/.config/openclaw-gcal/token-write.json \
  --port 18797
```

### 6. Google Calendar (readonly)

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  /home/desazure/.openclaw/workspace/skills/gcal-openclaw/scripts/auth_readonly.py \
  --account assistantdesi@gmail.com \
  --token ~/.config/openclaw-gcal/token-readonly.json \
  --port 18798
```

## Step 6: Verify (optional)

```bash
python3 /home/desazure/.openclaw/workspace/ops/google-auth/audit_google_oauth.py
```

## Troubleshooting

- **"Address already in use"**: Run `sudo fuser -k <port>/tcp` on the VM to free the port.
- **"Token has been expired or revoked"**: Delete the token file for that service (Step 4), then rerun the auth command.
- **Browser doesn't redirect**: Make sure the tunnel (Step 1) is still running on your Mac.
- **"Could not resolve hostname oclaw"**: You need Tailscale running on your Mac.

## Port Map

| Port  | Service              |
|-------|----------------------|
| 18793 | Gmail                |
| 18794 | Google Drive         |
| 18795 | Google Docs          |
| 18796 | Google Sheets        |
| 18797 | Google Calendar (write) |
| 18798 | Google Calendar (readonly) |
