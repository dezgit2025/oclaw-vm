#!/usr/bin/env python3

import argparse
from pathlib import Path

from googleapiclient.http import MediaIoBaseDownload

from _gdrive import assert_in_allowed_folder, build_drive


def main():
    ap = argparse.ArgumentParser(description="Download a file from Drive (restricted to OpenClawShared subtree).")
    ap.add_argument("--token", required=True)
    ap.add_argument("--file-id", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    dc = build_drive(args.token)
    assert_in_allowed_folder(dc.service, args.file_id)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    req = dc.service.files().get_media(fileId=args.file_id)
    with out.open("wb") as f:
        downloader = MediaIoBaseDownload(f, req)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download {int(status.progress() * 100)}%")

    print(f"OK: downloaded to {out}")


if __name__ == "__main__":
    main()
