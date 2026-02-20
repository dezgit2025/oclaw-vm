---
name: gmail-alerts
description: Send time-critical alert emails (restricted: only to desi4k@gmail.com).
user-invocable: true
metadata: {"openclaw":{"emoji":"🚨"}}
---

# Gmail Alerts (SEND) — restricted

This skill sends a **real email** via Gmail API.

## Safety restrictions

- Recipient is **hardcoded** to: `desi4k@gmail.com`
- Subject is prefixed with: `[OpenClaw ALERT] `
- Plain-text body only
- No attachments, no CC/BCC

## One-time OAuth setup (separate token)

This uses a **separate** OAuth token from gmail-drafts so drafts stay compose-only.

Create the token:

```bash
python3 {baseDir}/scripts/auth_alerts.py \
  --account desi4k@gmail.com \
  --token ~/.config/openclaw-gmail/token-alerts.json \
  --no-local-server
```

Notes:
- Requires `~/.config/openclaw-gmail/credentials.json`.
- `--no-local-server` prints a URL and prompts for a code (works on headless servers).

## Send an alert

```bash
python3 {baseDir}/scripts/send_alert.py \
  --token ~/.config/openclaw-gmail/token-alerts.json \
  --subject "Kimi proxy down" \
  --body "Health check failed 3x in a row."
```

## Trigger

If the user message starts with `alert:` (case-insensitive), treat the rest as the alert body.
