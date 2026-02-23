#!/usr/bin/env python3
"""NWS weather.gov alert checker for NYC (zone NYZ072).

- Pulls active alerts for zone NYZ072.
- Identifies 'major incidents' based on event types.
- Persists state so we can keep reminding until acknowledged.

This script prints a ready-to-send message.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

ZONE = "NYZ072"  # NYC/Manhattan forecast zone via api.weather.gov/points
STATE_PATH = Path(__file__).resolve().parents[1] / "state" / "weather_alert_state.json"

MAJOR_EVENTS = {
    "Blizzard Warning",
    "Winter Storm Warning",
    "Ice Storm Warning",
    "Coastal Flood Warning",
    "Coastal Flood Watch",
    "Flood Warning",
    "Flood Watch",
    "Flash Flood Warning",
    "Severe Thunderstorm Warning",
    "Tornado Warning",
    "High Wind Warning",
    "Hurricane Warning",
    "Tropical Storm Warning",
}

# We also treat some advisories as major if they mention >= 3 inches snow/rain in description
TEXT_THRESHOLD_IN = 3.0


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "last_checked": None,
        "acknowledged_ids": [],
        "shopping_done_for": {},
    }


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def fetch_alerts() -> list[dict]:
    url = f"https://api.weather.gov/alerts/active?zone={ZONE}"
    r = requests.get(url, timeout=20, headers={"User-Agent": "OpenClaw/NYCWeatherAlerts"})
    r.raise_for_status()
    return r.json().get("features", [])


def current_cached_major(state: dict) -> dict | None:
    """Return cached major alert (from last fetch), if present."""
    return state.get("current_major") or None


def extract_inches(text: str) -> list[float]:
    # Look for patterns like "3 to 7 inches" or "between 15 and 20 inches" or "3 inches"
    t = text.lower()
    nums = []

    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:to|–|-|and)\s*(\d+(?:\.\d+)?)\s*inch", t):
        nums.extend([float(m.group(1)), float(m.group(2))])

    for m in re.finditer(r"(?:between\s+)?(\d+(?:\.\d+)?)\s*inch", t):
        nums.append(float(m.group(1)))

    return nums


def is_major(alert_props: dict) -> bool:
    event = alert_props.get("event")
    if event in MAJOR_EVENTS:
        return True

    desc = alert_props.get("description") or ""
    inches = extract_inches(desc)
    if inches and max(inches) >= TEXT_THRESHOLD_IN:
        # Could be snow or rain; still worth surfacing as major.
        return True

    return False


def summarize(alert_props: dict) -> str:
    event = alert_props.get("event") or "(Unknown event)"
    headline = alert_props.get("headline") or ""
    onset = alert_props.get("onset")
    ends = alert_props.get("ends")
    desc = alert_props.get("description") or ""

    # Pull the WHAT/WHEN lines if present
    lines = [l.strip() for l in desc.splitlines() if l.strip()]
    what = next((l for l in lines if l.startswith("* WHAT")), None)
    when = next((l for l in lines if l.startswith("* WHEN")), None)

    parts = [f"{event}"]
    if headline:
        parts.append(f"- {headline}")
    if what:
        parts.append(what)
    if when:
        parts.append(when)
    if onset:
        parts.append(f"Onset: {onset}")
    if ends:
        parts.append(f"Ends: {ends}")

    return "\n".join(parts)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--remind",
        action="store_true",
        help="Do not call weather.gov. Only re-send reminders for the last cached major alert until acknowledged.",
    )
    ap.add_argument(
        "--update-only",
        action="store_true",
        help="Call weather.gov and print output only if the major alert details changed since last fetch (storm-mode updates).",
    )
    args = ap.parse_args()

    state = load_state()
    state["last_checked"] = now_utc_iso()

    major = []
    if args.remind:
        cached = current_cached_major(state)
        if cached:
            major = [cached]
    else:
        alerts = fetch_alerts()
        for feat in alerts:
            props = feat.get("properties") or {}
            if is_major(props):
                major.append({"id": props.get("id"), "props": props})

    # sort: severity then onset
    def sev_rank(p: dict) -> int:
        sev = (p.get("severity") or "").lower()
        return {"extreme": 0, "severe": 1, "moderate": 2, "minor": 3}.get(sev, 9)

    major.sort(key=lambda a: (sev_rank(a["props"]), a["props"].get("onset") or ""))

    unacked = [a for a in major if a.get("id") and a["id"] not in set(state.get("acknowledged_ids", []))]

    if not major:
        # Clear cached major only when we actually checked the API.
        if not args.remind:
            state["current_major"] = None
        save_state(state)
        print("NYC Weather: No major NWS alerts right now.")
        return

    # If everything is acknowledged, stay quiet-ish but still show current major alerts.
    focus = unacked[0] if unacked else major[0]
    alert_id = focus.get("id")

    # Cache the focus alert when we actually checked weather.gov.
    if not args.remind:
        state["current_major"] = focus

    # Compute a lightweight signature to detect updates across fetches.
    props = focus.get("props") or {}
    signature = {
        "id": alert_id,
        "sent": props.get("sent"),
        "effective": props.get("effective"),
        "headline": props.get("headline"),
        "ends": props.get("ends"),
    }

    prev_sig = state.get("current_major_signature")
    changed = prev_sig != signature
    if not args.remind:
        state["current_major_signature"] = signature

    if args.update_only and not changed:
        save_state(state)
        # Silent when no update.
        return

    msg = []
    msg.append("NYC Major Weather Alert (NWS/weather.gov)")
    if args.update_only and changed:
        msg[0] = "NYC Major Weather Alert UPDATE (NWS/weather.gov)"
    msg.append(summarize(focus["props"]))

    if unacked:
        msg.append("\nReply: **acknowledge weather** to stop repeated reminders for this incident.")
        # shopping check
        shopping_done = bool(state.get("shopping_done_for", {}).get(alert_id))
        if not shopping_done:
            msg.append("\nQuick storm checklist:")
            msg.append("- Did you go shopping for food / essentials yet? Reply YES / NO.")
            msg.append("- Charge your phone(s) now.")
            msg.append("- Charge your battery packs / power banks.")

    save_state(state)
    print("\n".join(msg))


if __name__ == "__main__":
    main()
