#!/usr/bin/env python3

"""Move a file into a subfolder under OpenClawShared.

- Refuses to operate on files outside OpenClawShared.
- Refuses to move into a folder outside OpenClawShared.

Requires Drive scope token.
"""

from __future__ import annotations

import argparse

from _gdrive import assert_in_allowed_folder, build_drive


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--file-id", required=True)
    ap.add_argument("--folder-id", required=True)
    args = ap.parse_args()

    drive = build_drive(args.token).service

    # Enforce both ends are inside OpenClawShared
    assert_in_allowed_folder(drive, args.file_id)
    assert_in_allowed_folder(drive, args.folder_id)

    meta = drive.files().get(fileId=args.file_id, fields="id,parents,name").execute()
    parents = meta.get("parents") or []

    # Add new parent; remove existing parents (within OpenClawShared) to keep it tidy.
    remove_parents = ",".join(parents) if parents else None
    resp = drive.files().update(
        fileId=args.file_id,
        addParents=args.folder_id,
        removeParents=remove_parents,
        fields="id,parents,name",
    ).execute()

    print(f"OK: moved file id={resp.get('id')} name={resp.get('name')} into folder={args.folder_id}")


if __name__ == "__main__":
    main()
