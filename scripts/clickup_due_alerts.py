#!/usr/bin/env python3

"""ClickUp due/overdue monitor for a single list.

Design goals:
- Minimal dependencies (requests)
- Low cost: no LLM usage; intended to be called from OpenClaw cron.
- Emits one of:
  - NO_ALERT
  - ALERT: <human-readable text>

Alert policy:
- Always: tasks due in the next 2 hours.
- Overdue:
  - If tagged `urgent`: repeat every 60 minutes until completed.
  - Otherwise: send a daily reminder at 11am ET.

De-dupe:
- Will not repeat the same task alert more than once per run window unless status changed.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

CLICKUP_TOKEN_PATH = Path.home() / ".config" / "openclaw-clickup" / "token"
CLICKUP_DEFAULT_PATH = Path.home() / ".config" / "openclaw-clickup" / "default.json"
STATE_PATH = Path.home() / ".config" / "openclaw-clickup" / "alerts_state.json"

API = "https://api.clickup.com/api/v2"


@dataclass
class AlertTask:
    task_id: str
    name: str
    url: str
    due_ms: int
    status: str  # overdue | due_soon


def now_ms() -> int:
    return int(time.time() * 1000)


def load_token() -> str:
    if not CLICKUP_TOKEN_PATH.exists():
        raise SystemExit(f"Missing ClickUp token at {CLICKUP_TOKEN_PATH}")
    return CLICKUP_TOKEN_PATH.read_text().strip()


def load_list_ids() -> dict[str, str]:
    """Return mapping of logical list names to ClickUp list IDs.

    Backwards compatible:
    - If default.json contains `listId`, that is treated as the primary `tasks` list.
    - If it contains `listIds` (dict), those are used.
    - If it contains `listIds` (list), they are treated as unnamed lists.
    """

    if not CLICKUP_DEFAULT_PATH.exists():
        raise SystemExit(f"Missing ClickUp default.json at {CLICKUP_DEFAULT_PATH}")

    obj = json.loads(CLICKUP_DEFAULT_PATH.read_text())

    # Preferred: explicit mapping
    li = obj.get("listIds")
    if isinstance(li, dict) and li:
        return {str(k): str(v) for k, v in li.items() if v}

    # Fallback: legacy single list
    if obj.get("listId"):
        return {"tasks": str(obj["listId"])}

    # Fallback: list of ids
    if isinstance(li, list) and li:
        out = {}
        for i, v in enumerate(li):
            if v:
                out[f"list{i+1}"] = str(v)
        if out:
            return out

    raise SystemExit("Missing ClickUp listId(s) in default.json")


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"lastAlerts": {}, "lastSentAt": {}}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"lastAlerts": {}, "lastSentAt": {}}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True))


def has_tag(task: dict, tag_name: str) -> bool:
    tags = task.get("tags") or []
    want = (tag_name or "").strip().lower()
    for t in tags:
        name = (t.get("name") or "").strip().lower()
        if name == want:
            return True
    return False


def list_tasks(session: requests.Session, list_id: str, due_lt_ms: int) -> list[dict]:
    # ClickUp supports due_date_lt/gt as ms timestamps.
    params = {
        "include_closed": "false",
        "due_date_lt": str(due_lt_ms),
        # We can't reliably filter overdue only via API without two calls; we filter locally.
        "subtasks": "true",
    }
    r = session.get(f"{API}/list/{list_id}/task", params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("tasks") or []


def list_all_tasks(session: requests.Session, list_ids: dict[str, str], due_lt_ms: int) -> list[dict]:
    """Fetch tasks for all configured lists and annotate with `_oclaw_list` name."""
    out: list[dict] = []
    for name, lid in list_ids.items():
        try:
            tasks = list_tasks(session, lid, due_lt_ms=due_lt_ms)
        except Exception as e:
            # Best-effort: keep monitoring other lists.
            print(f"WARN: failed to fetch list {name} ({lid}): {e}")
            continue
        for t in tasks:
            t["_oclaw_list"] = name
            out.append(t)
    return out


def select_alerts(tasks: list[dict], *, now: int, mode: str) -> list[AlertTask]:
    """Select alerts.

    mode:
      - "frequent": due soon + overdue(urgent only)
      - "daily": overdue(non-urgent only)

    List policy:
      - `habits` list: due-soon only; no overdue nagging.
    """

    soon_horizon = now + 2 * 60 * 60 * 1000

    out: list[AlertTask] = []
    for t in tasks:
        due = t.get("due_date")
        if due is None:
            continue
        try:
            due_ms = int(due)
        except Exception:
            continue

        list_name = str(t.get("_oclaw_list") or "tasks")
        is_habits = list_name.strip().lower() == "habits"

        urgent = has_tag(t, "urgent")
        overdue = due_ms < now

        status = None
        if mode == "frequent":
            if due_ms <= soon_horizon and not overdue:
                status = "due_soon"
            elif overdue and urgent and not is_habits:
                status = "overdue"
        elif mode == "daily":
            if overdue and not urgent and not is_habits:
                status = "overdue"
        else:
            raise SystemExit(f"Unknown mode: {mode}")

        if not status:
            continue

        # Include list label in task_id key to avoid collisions across lists.
        tid = str(t.get("id"))
        task_key = f"{list_name}:{tid}"

        out.append(
            AlertTask(
                task_id=task_key,
                name=f"[{list_name}] {str(t.get('name'))}",
                url=str(t.get("url")),
                due_ms=due_ms,
                status=status,
            )
        )

    pri = {"overdue": 0, "due_soon": 1}
    out.sort(key=lambda x: (pri.get(x.status, 9), x.due_ms))
    return out


def dedupe(alerts: list[AlertTask], state: dict[str, Any], *, now: int, mode: str) -> list[AlertTask]:
    """De-dupe policy.

    - For frequent mode:
      - due_soon alerts are edge-triggered (only when due/status changes)
      - overdue urgent alerts can repeat on a cooldown (60 minutes)
    - For daily mode:
      - always send overdue non-urgent each day (no dedupe)
    """

    if mode == "daily":
        return alerts

    last_sig = state.setdefault("lastAlerts", {})
    last_sent = state.setdefault("lastSentAt", {})

    keep: list[AlertTask] = []
    for a in alerts:
        key = a.task_id
        cur_sig = f"{a.status}:{a.due_ms}"

        if a.status == "overdue":
            # overdue in frequent mode implies urgent. Repeat every 60 minutes.
            prev_sent = int(last_sent.get(key) or 0)
            if now - prev_sent < 60 * 60 * 1000:
                continue
            last_sent[key] = now
            last_sig[key] = cur_sig
            keep.append(a)
            continue

        # due_soon: edge-triggered
        prev = last_sig.get(key)
        if prev == cur_sig:
            continue
        last_sig[key] = cur_sig
        last_sent[key] = now
        keep.append(a)

    # GC
    if len(last_sig) > 5000:
        keep_ids = {a.task_id for a in alerts}
        state["lastAlerts"] = {k: v for k, v in last_sig.items() if k in keep_ids}
        state["lastSentAt"] = {k: v for k, v in last_sent.items() if k in keep_ids}

    return keep


def fmt_ms(ms: int) -> str:
    """Format ms timestamp in America/New_York.

    Rationale: alerts should read in local time (ET) since that’s how due dates are interpreted.
    """

    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        dt = datetime.fromtimestamp(ms / 1000, tz=ZoneInfo("America/New_York"))
        # Example: 2026-02-22 12:13 PM ET
        return dt.strftime("%Y-%m-%d %I:%M %p ET")
    except Exception:
        # Fallback to UTC if zoneinfo is unavailable.
        return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(ms / 1000))


def main():
    import os

    ap_mode = os.environ.get("CLICKUP_ALERT_MODE", "frequent").strip().lower()

    token = load_token()
    list_ids = load_list_ids()
    state = load_state()

    now = now_ms()

    s = requests.Session()
    s.headers.update({"Authorization": token})

    # Use 7d lookahead so we always include overdue tasks as well.
    tasks = list_all_tasks(s, list_ids, due_lt_ms=now + 7 * 24 * 60 * 60 * 1000)

    alerts = select_alerts(tasks, now=now, mode=ap_mode)
    alerts = dedupe(alerts, state, now=now, mode=ap_mode)
    save_state(state)

    if not alerts:
        print("NO_ALERT")
        return

    lines = []
    lines.append(f"ClickUp alerts ({ap_mode}; {fmt_ms(now)}):")
    for a in alerts[:20]:
        lines.append(f"- [{a.status}] {a.name} (due {fmt_ms(a.due_ms)})")
        lines.append(f"  {a.url}")

    if len(alerts) > 20:
        lines.append(f"(+{len(alerts)-20} more)")

    print("ALERT: " + "\n".join(lines))


if __name__ == "__main__":
    main()
