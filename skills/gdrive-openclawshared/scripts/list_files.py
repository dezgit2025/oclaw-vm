#!/usr/bin/env python3

import argparse

from _gdrive import ALLOWED_FOLDER_ID, build_drive


def main():
    ap = argparse.ArgumentParser(description="List files in the OpenClawShared Drive folder.")
    ap.add_argument("--token", required=True)
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    dc = build_drive(args.token)
    q = f"'{ALLOWED_FOLDER_ID}' in parents and trashed=false"
    resp = (
        dc.service.files()
        .list(
            q=q,
            pageSize=args.limit,
            fields="files(id,name,mimeType,modifiedTime,size)",
            orderBy="modifiedTime desc",
        )
        .execute()
    )

    files = resp.get("files") or []
    if not files:
        print("(no files)")
        return

    for f in files:
        print(f"{f.get('id')}\t{f.get('name')}\t{f.get('mimeType')}\t{f.get('modifiedTime')}")


if __name__ == "__main__":
    main()
