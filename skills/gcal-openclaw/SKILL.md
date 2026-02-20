---
name: gcal-openclaw
description: Read and create Google Calendar events on a dedicated "OpenClaw" calendar (no attendee invites by default).
user-invocable: true
metadata: {"openclaw":{"emoji":"🗓️"}}
---

# Google Calendar — dedicated "OpenClaw" calendar

We will use a dedicated calendar named **OpenClaw**.

Safety rails:
- Default behavior: **create events with NO attendees** (no invites).
- Any future attendee-invite functionality must require explicit user confirmation.

## One-time setup

### Enable Google Calendar API (once)
https://console.developers.google.com/apis/api/calendar-json.googleapis.com/overview?project=721049927451

### OAuth tokens
We use **two** token files:
- Read-only: `~/.config/openclaw-gcal/token-readonly.json` (scope: calendar.readonly)
- Write: `~/.config/openclaw-gcal/token-write.json` (scope: calendar.events)

Copy OAuth client JSON:
- `~/.config/openclaw-gcal/credentials.json`

Tunnel from your Mac:

```bash
ssh -N -L 18797:127.0.0.1:18797 <your-vm-ssh-host>
```

Auth (read-only):

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/auth_readonly.py \
  --account desi4k@gmail.com \
  --token ~/.config/openclaw-gcal/token-readonly.json \
  --port 18797
```

Auth (write):

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/auth_write.py \
  --account desi4k@gmail.com \
  --token ~/.config/openclaw-gcal/token-write.json \
  --port 18797
```

## Initialize calendar

Creates the OpenClaw calendar if missing and prints its calendarId:

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/init_calendar.py \
  --token ~/.config/openclaw-gcal/token-write.json
```

## Create an event (no invites)

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python {baseDir}/scripts/create_event.py \
  --token ~/.config/openclaw-gcal/token-write.json \
  --calendar-id <calendarId> \
  --summary "Test" \
  --start "2026-02-10T15:00:00-05:00" \
  --end   "2026-02-10T15:30:00-05:00" \
  --description "notes"
```
