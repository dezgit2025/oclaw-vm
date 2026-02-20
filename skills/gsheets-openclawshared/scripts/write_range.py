#!/usr/bin/env python3

import argparse
import json

from _common import assert_in_allowed_folder, build_services


def main():
    ap = argparse.ArgumentParser(description="Write values to a Google Sheet range (restricted to OpenClawShared folder).")
    ap.add_argument("--token", required=True)
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--range", required=True)
    ap.add_argument(
        "--values",
        required=True,
        help='JSON array-of-arrays, e.g. [["A","B"],["1","2"]]',
    )
    args = ap.parse_args()

    values = json.loads(args.values)

    drive, sheets = build_services(args.token)
    assert_in_allowed_folder(drive, args.sheet_id)

    body = {"values": values}
    res = (
        sheets.spreadsheets()
        .values()
        .update(
            spreadsheetId=args.sheet_id,
            range=args.range,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    print("OK: updated", res.get("updatedRange"), "cells", res.get("updatedCells"))


if __name__ == "__main__":
    main()
