#!/usr/bin/env python3

"""Create a subfolder under OpenClawShared.

Hard-restricted to create only under the OpenClawShared allowed folder.
"""

from __future__ import annotations

import argparse

from _gdrive import ALLOWED_FOLDER_ID, build_drive


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--name", required=True)
    args = ap.parse_args()

    drive = build_drive(args.token).service

    meta = {
        "name": args.name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [ALLOWED_FOLDER_ID],
    }
    resp = drive.files().create(body=meta, fields="id,name").execute()
    print(f"OK: created folder id={resp.get('id')} name={resp.get('name')}")


if __name__ == "__main__":
    main()
