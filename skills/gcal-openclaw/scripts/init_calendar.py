#!/usr/bin/env python3

import argparse

from _common import build_calendar

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]

TARGET_NAME = "OpenClaw"


def main():
    ap = argparse.ArgumentParser(description="Create/find the dedicated 'OpenClaw' calendar.")
    ap.add_argument("--token", required=True)
    args = ap.parse_args()

    svc = build_calendar(args.token, SCOPES).cal

    page_token = None
    while True:
        resp = svc.calendarList().list(pageToken=page_token).execute()
        for cal in resp.get("items") or []:
            if cal.get("summary") == TARGET_NAME:
                cal_id = cal.get("id")
                print(f"OK: found calendarId={cal_id}")
                return
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    created = svc.calendars().insert(body={"summary": TARGET_NAME, "timeZone": "America/New_York"}).execute()
    print(f"OK: created calendarId={created.get('id')}")


if __name__ == "__main__":
    main()
