---
name: gmail-drafts
description: Create Gmail draft emails (not send) via the Gmail API on Linux using OAuth credentials.json + token.json. Use when the user wants the agent to write a draft into their Gmail account, list drafts, or delete drafts.
---

# Gmail Drafts (OAuth)

This skill stores drafts in the user's Gmail account (it does **not** send).

## One-time setup (user does this)

1) Create a Google Cloud project + OAuth client (Desktop app).
2) Download the OAuth client JSON as `credentials.json`.
3) Place files on the Linux host:

- `~/.config/openclaw-gmail/credentials.json`
- (generated later) `~/.config/openclaw-gmail/token-<account>.json` (falls back to legacy `token.json` if present)

4) Run auth to create a token file (default: `token-<account>.json`):

```bash
python3 /home/desazure/.openclaw/workspace/skills/gmail-drafts/scripts/auth.py \
  --account you@gmail.com
```

## Create a draft

```bash
python3 /home/desazure/.openclaw/workspace/skills/gmail-drafts/scripts/create_draft.py \
  --account you@gmail.com \
  --to "person@example.com" \
  --subject "Subject" \
  --body-file /path/to/body.md
```

Token selection:
- Default: `~/.config/openclaw-gmail/token-<account>.json`
- Fallback: `~/.config/openclaw-gmail/token.json` (legacy)

## Notes

- OAuth scopes are restricted to *compose only* (`gmail.compose`).
- Drafts appear in Gmail under Drafts immediately.
- For safety, never send from this skill; only draft operations are supported.
