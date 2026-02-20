#!/usr/bin/env python3

import argparse
from pathlib import Path

from googleapiclient.http import MediaFileUpload

from _gdrive import ALLOWED_FOLDER_ID, build_drive


def main():
    ap = argparse.ArgumentParser(description="Upload a local file into OpenClawShared folder.")
    ap.add_argument("--token", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--name", default=None, help="Optional Drive filename override")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        raise SystemExit(f"Missing file: {p}")

    dc = build_drive(args.token)

    file_metadata = {"name": args.name or p.name, "parents": [ALLOWED_FOLDER_ID]}
    media = MediaFileUpload(str(p), resumable=True)

    created = dc.service.files().create(body=file_metadata, media_body=media, fields="id,name").execute()
    print(f"OK: uploaded id={created.get('id')} name={created.get('name')}")


if __name__ == "__main__":
    main()
