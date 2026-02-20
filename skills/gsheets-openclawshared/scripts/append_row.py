#!/usr/bin/env python3

import argparse
import json

from _common import assert_in_allowed_folder, build_services


def main():
    ap = argparse.ArgumentParser(description="Append a row to a Google Sheet (restricted to OpenClawShared folder).")
    ap.add_argument("--token", required=True)
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--range", required=True, help='Target range, e.g. "Sheet1!A:Z"')
    ap.add_argument("--row", required=True, help='JSON array, e.g. ["2026-02-09","note"]')
    args = ap.parse_args()

    row = json.loads(args.row)

    drive, sheets = build_services(args.token)
    assert_in_allowed_folder(drive, args.sheet_id)

    body = {"values": [row]}
    res = (
        sheets.spreadsheets()
        .values()
        .append(
            spreadsheetId=args.sheet_id,
            range=args.range,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )

    updates = res.get("updates") or {}
    print("OK: appended", updates.get("updatedRange"))


if __name__ == "__main__":
    main()
