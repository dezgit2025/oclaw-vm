# ClickUp Alerts — Due / Overdue

This workspace runs ClickUp due/overdue monitoring via cron.

## What it monitors
- ClickUp list IDs configured in:
  - `~/.config/openclaw-clickup/default.json`
    - legacy: `listId` (single list)
    - current: `listIds` (mapping: `tasks`, `bills`, `habits`)
- Uses token:
  - `~/.config/openclaw-clickup/token`

Script:
- `scripts/clickup_due_alerts.py`

## Alert policy (logic)
The script prints either `NO_ALERT` or `ALERT: ...`.

### List-level policy
- `habits` list: **due-soon only**. No overdue nagging (even if tagged urgent).
- `tasks` + `bills`: normal policy.

### Frequent checks (mode: `frequent`)
Default mode when `CLICKUP_ALERT_MODE` is unset.

Emits alerts for:
- **Due soon**: tasks due in the **next 2 hours** (edge-triggered; won’t repeat every run unless due/status changes)
- **Overdue + urgent**: overdue tasks tagged `urgent`
  - repeats with a **60 minute cooldown** until resolved

### Overdue reminders (mode: `daily`)
When run with `CLICKUP_ALERT_MODE=daily`, emits alerts for:
- **Overdue non-urgent** tasks only

## Urgent vs non-urgent
- A task is treated as **urgent** if it has a ClickUp tag named `urgent` (case-insensitive).
- Overdue urgent tasks alert more aggressively (hourly cooldown in frequent mode).
- Overdue non-urgent tasks are summarized on the scheduled reminder runs (daily-mode cron).

### Bills default
Policy decision: tasks in the `bills` list should default to **Urgent** (set ClickUp Priority=Urgent and/or tag `urgent`).

Note: our alerting logic keys off the **tag** `urgent`.

## Cron schedules
There are two relevant jobs:

1) Frequent monitor (every ~18 minutes)
- Job name: `ClickUp due/overdue monitor (18m) → email alert`
- Schedule: `every 1,080,000 ms` (18m)
- Purpose: due-soon + overdue-urgent

2) Overdue non-urgent reminders (2x/day)
- Job name: `ClickUp overdue daily reminder (11am ET) → email alert`
- Schedule (America/New_York): **11:07am ET and 4:07pm ET**
- Cron expr: `7 11,16 * * *`
- Purpose: overdue non-urgent reminders

The 7-minute offset is intentional to reduce cron collisions with on-the-hour jobs.

## Dedupe behavior
Alert times are displayed in **ET (America/New_York)** and use **12-hour AM/PM** formatting.

State is stored at:
- `~/.config/openclaw-clickup/alerts_state.json`

Policy:
- `due_soon` alerts are edge-triggered (by signature `status:due_ms`).
- `overdue` in frequent mode repeats only after 60 minutes since last send.
- `daily` mode does not dedupe; it’s intended to remind again on the next scheduled run if still overdue.

## How to change behavior
- Adjust windows/cooldowns in `scripts/clickup_due_alerts.py`.
- Adjust schedule via `cron update`.

## Testing
Manual run (prints alerts to stdout):
- `CLICKUP_ALERT_MODE=daily /home/desazure/.venv-clickup/bin/python /home/desazure/.openclaw/workspace/scripts/clickup_due_alerts.py`

