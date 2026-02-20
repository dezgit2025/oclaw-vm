#!/usr/bin/env python3

import argparse
import json

from _common import assert_in_allowed_folder, build_services


def main():
    ap = argparse.ArgumentParser(description="Read a range from a Google Sheet (restricted to OpenClawShared folder).")
    ap.add_argument("--token", required=True)
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--range", required=True)
    args = ap.parse_args()

    drive, sheets = build_services(args.token)
    assert_in_allowed_folder(drive, args.sheet_id)

    resp = sheets.spreadsheets().values().get(spreadsheetId=args.sheet_id, range=args.range).execute()
    print(json.dumps(resp.get("values") or [], ensure_ascii=False))


if __name__ == "__main__":
    main()
