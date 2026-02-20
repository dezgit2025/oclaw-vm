#!/usr/bin/env python3

import argparse

from _common import build_calendar

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def main():
    ap = argparse.ArgumentParser(description="Create an event on a specific calendar (NO attendees/invites).")
    ap.add_argument("--token", required=True)
    ap.add_argument("--calendar-id", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--start", required=True, help="RFC3339 datetime with TZ, e.g. 2026-02-10T15:00:00-05:00")
    ap.add_argument("--end", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument(
        "--popup-minutes",
        type=int,
        default=None,
        help="Add a popup reminder N minutes before start (e.g. 0 for at-start).",
    )
    args = ap.parse_args()

    svc = build_calendar(args.token, SCOPES).cal

    event = {
        "summary": args.summary,
        "description": args.description,
        "start": {"dateTime": args.start},
        "end": {"dateTime": args.end},
        # Safety rail: no attendees field at all.
    }

    if args.popup_minutes is not None:
        event["reminders"] = {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": int(args.popup_minutes)}],
        }

    created = svc.events().insert(calendarId=args.calendar_id, body=event, sendUpdates="none").execute()
    print(f"OK: created eventId={created.get('id')} htmlLink={created.get('htmlLink')}")


if __name__ == "__main__":
    main()
