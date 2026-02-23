# NYC Major Weather Alerts (weather.gov) — Skill + Cron

This document describes the NYC weather incident alerting workflow implemented in OpenClaw.

## Purpose
- Use **official NWS/weather.gov** alerts for NYC.
- Notify user about **major incidents** (snowstorms, blizzard, flooding, high wind, severe storms).
- Avoid spam when there is no incident.
- During an active incident, keep reminding the user until they **acknowledge**.

## Skill
- Skill folder: `skills/weather-storm-alerts-nyc/`
- Entry doc: `skills/weather-storm-alerts-nyc/SKILL.md`
- Main script: `skills/weather-storm-alerts-nyc/scripts/check_nws_alerts_nyc.py`
- State file: `skills/weather-storm-alerts-nyc/state/weather_alert_state.json`

### Data source
- NWS API endpoint (zone-based):
  - `https://api.weather.gov/alerts/active?zone=NYZ072`
- Zone: **NYZ072** (NYC/Manhattan forecast zone as resolved via `api.weather.gov/points` for Greenwich Village coords).

### Major-incident detection
The script treats an alert as “major” if:
- `event` is one of:
  - Blizzard Warning
  - Winter Storm Warning
  - Ice Storm Warning
  - Coastal Flood Warning / Watch
  - Flood Warning / Watch
  - Flash Flood Warning
  - Severe Thunderstorm Warning
  - Tornado Warning
  - High Wind Warning
  - Hurricane Warning
  - Tropical Storm Warning
- OR the description text contains an inches amount ≥ **3"** (heuristic fallback).

### Output behavior
- Normal check prints either:
  - `NYC Weather: No major NWS alerts right now.`
  - or `NYC Major Weather Alert (NWS/weather.gov)` with headline + onset/ends + key lines.

### Acknowledgement
User can stop repeated reminders for the current incident by replying:
- **"acknowledge weather"** (or similar phrasing).

### Storm checklist included in unacknowledged alerts
When an incident is active and unacknowledged, the message includes:
- Shopping prompt (YES/NO)
- Charge phone(s)
- Charge battery packs / power banks

## Cron jobs

### 1) Daily baseline check (weather.gov)
- Purpose: check once/day for major incidents.
- Schedule: **08:00 AM ET**
- Job id: `1bbd1b63-22d1-4c5a-8566-8c8ea44b5d4c`

Notes:
- Only sends a message if there is a major alert.

### 2) Storm-mode update polling (weather.gov)
- Purpose: if a major alert is active, re-check NWS for **updates**.
- Schedule: **every 3 hours** (ET)
- Job id: `bd4acb03-11f7-4906-a673-392e97213412`

Implementation:
- Uses `check_nws_alerts_nyc.py --update-only`
- Script compares a lightweight signature (id/sent/effective/headline/ends) and only prints/sends when changed.

### 3) Reminder nags until acknowledgement (cached)
- Purpose: ensure user sees the incident; repeats even if NWS has no update.
- Schedule: **1:00 PM + 7:00 PM ET**
- Job id: `b7ed7793-4a29-4af5-98c8-75db816c8ba0`

Implementation:
- Uses `check_nws_alerts_nyc.py --remind`
- Does **not** call weather.gov; re-sends cached incident details until acknowledged.

## Operator notes
- This workflow intentionally separates:
  - **fetching/updating** (weather.gov API calls), from
  - **nagging/reminders** (cached re-send)
  to reduce API usage while keeping the user informed.

