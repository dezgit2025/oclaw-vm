#!/usr/bin/env python3

"""Create a Google Spreadsheet inside the OpenClawShared Drive folder.

Uses Drive API (scope: drive) and hard-restricts parent folder.
"""

from __future__ import annotations

import argparse

from _gdrive import ALLOWED_FOLDER_ID, build_drive


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True, help="Drive token JSON (scope: drive)")
    ap.add_argument("--name", required=True, help="Spreadsheet name")
    args = ap.parse_args()

    drive = build_drive(args.token).service

    meta = {
        "name": args.name,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [ALLOWED_FOLDER_ID],
    }

    resp = drive.files().create(body=meta, fields="id,name,webViewLink").execute()

    file_id = resp.get("id")
    link = resp.get("webViewLink")
    name = resp.get("name")

    print(f"OK: created spreadsheet id={file_id} name={name}")
    if link:
        print(link)


if __name__ == "__main__":
    main()
