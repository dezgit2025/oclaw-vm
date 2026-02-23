---
name: weather-storm-alerts-nyc
description: NYC major weather incident alerting using weather.gov (NWS). Checks for active NWS alerts and sends reminders 3x/day until acknowledged; also asks whether you shopped for food.
user-invocable: true
---

# Weather Storm Alerts (NYC)

This skill supports major weather incident monitoring for New York City using the official NWS weather.gov API.

## What it does
- Checks active NWS alerts for the NYC forecast zone (**NYZ072**; Manhattan/NYC area) and reports headline + key details.
- Filters for major incident types (e.g., Blizzard Warning, Winter Storm Warning, Flood Watch/Warning, Severe Thunderstorm Warning, Tornado Warning, High Wind Warning, Coastal Flood Warning).
- Runs on a schedule (3x/day) and **repeats** until the user acknowledges.
- While an unacknowledged major incident is active, it asks: **“Did you go shopping for food?”**

## Files
- Script: `scripts/check_nws_alerts_nyc.py`
- State: `state/weather_alert_state.json`

## Acknowledgement
When user says something like:
- “acknowledge weather” / “ack storm” / “acknowledge”

…mark the current incident as acknowledged in the state file so reminders stop.

If user answers shopping question (“yes I went shopping” / “done”), mark `shopping_done=true` in state.
