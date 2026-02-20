#!/usr/bin/env python3

"""Keep only the newest N Instagram downloads in workspace.

Default target dir:
  /home/desazure/.openclaw/workspace/instagram/out

We consider a "download" to be a base name like:
  <timestamp>_<shortcode>
and we keep associated files with that prefix, e.g.:
  .mp4, .mkv, .webm, .info.json

This avoids leaving orphan .info.json files behind.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

MEDIA_EXTS = {".mp4", ".mkv", ".webm"}


def infer_group_key(p: Path) -> str:
    """Group by prefix before known suffixes.

    Examples:
      20260215T071723Z_DUuJv3GEbCL.mp4 -> 20260215T071723Z_DUuJv3GEbCL
      20260215T071723Z_DUuJv3GEbCL.info.json -> 20260215T071723Z_DUuJv3GEbCL
    """
    name = p.name
    if name.endswith(".info.json"):
        return name[: -len(".info.json")]
    return p.stem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dir",
        default="/home/desazure/.openclaw/workspace/instagram/out",
        help="Directory containing IG downloads",
    )
    ap.add_argument("--keep", type=int, default=30, help="Number of newest downloads to keep")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = Path(args.dir)
    root.mkdir(parents=True, exist_ok=True)

    files = [p for p in root.iterdir() if p.is_file()]
    if not files:
        print("OK: no files")
        return

    # Build groups keyed by base name.
    groups: dict[str, list[Path]] = {}
    for p in files:
        # only manage the types we produce
        if p.suffix in MEDIA_EXTS or p.name.endswith(".info.json"):
            groups.setdefault(infer_group_key(p), []).append(p)

    # Determine group recency by newest mtime in the group.
    group_items = []
    for key, ps in groups.items():
        newest = max(p.stat().st_mtime for p in ps)
        group_items.append((newest, key, ps))

    group_items.sort(reverse=True, key=lambda t: t[0])
    keep = set(k for _, k, _ in group_items[: args.keep])

    to_delete: list[Path] = []
    for _, key, ps in group_items[args.keep :]:
        for p in ps:
            to_delete.append(p)

    if args.dry_run:
        print(f"DRY_RUN: groups_total={len(group_items)} keep={args.keep} delete_files={len(to_delete)}")
        for p in to_delete[:50]:
            print(f"DELETE: {p}")
        if len(to_delete) > 50:
            print(f"... and {len(to_delete)-50} more")
        return

    deleted = 0
    for p in to_delete:
        try:
            p.unlink()
            deleted += 1
        except FileNotFoundError:
            pass

    print(f"OK: groups_total={len(group_items)} kept={min(args.keep, len(group_items))} deleted_files={deleted}")


if __name__ == "__main__":
    main()
