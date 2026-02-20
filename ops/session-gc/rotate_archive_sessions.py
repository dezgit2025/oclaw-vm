#!/usr/bin/env python3
"""Rotate + archive OpenClaw session log backups.

What it does:
1) Runs session_gc.py to truncate oversized session *.jsonl files (>max_mb) down to ~target_mb.
   - Backups are written into ARCHIVE_ROOT/YYYY-MM-DD/ (UTC) to keep sessions dir tidy.
2) Moves any existing *.backup-* files that are still sitting next to session *.jsonl into the archive.
3) Gzips archived backups.
4) Retention: deletes archived backup files older than KEEP_DAYS.

Safe by default: does NOT delete active session *.jsonl files.
"""

from __future__ import annotations

import argparse
import gzip
import os
import shutil
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path


def utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def gzip_file(src: Path) -> Path:
    if src.suffix == ".gz":
        return src
    dst = src.with_name(src.name + ".gz")
    with src.open("rb") as f_in, gzip.open(dst, "wb", compresslevel=6) as f_out:
        shutil.copyfileobj(f_in, f_out)
    src.unlink(missing_ok=True)
    return dst


def iter_backup_files(root: Path):
    yield from root.glob("*.backup-*")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--sessions-dir",
        default=str(Path.home() / ".openclaw" / "agents" / "main" / "sessions"),
    )
    ap.add_argument(
        "--archive-root",
        default=str(Path.home() / ".openclaw" / "agents" / "main" / "sessions" / "archive"),
    )
    ap.add_argument("--max-mb", type=float, default=5.0)
    ap.add_argument("--target-mb", type=float, default=3.0)
    ap.add_argument("--keep-days", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sessions_dir = Path(args.sessions_dir).expanduser()
    archive_root = Path(args.archive_root).expanduser()
    today_dir = archive_root / utc_date()

    session_gc = Path(__file__).resolve().parent / "session_gc.py"
    if not session_gc.exists():
        raise SystemExit(f"Missing session_gc.py next to rotate script: {session_gc}")

    if not sessions_dir.exists():
        raise SystemExit(f"No sessions dir: {sessions_dir}")

    print(f"sessions_dir={sessions_dir}")
    print(f"archive_root={archive_root}")
    print(f"today_archive={today_dir}")

    # 1) Run session GC (writes backups into archive)
    cmd = [
        str(session_gc),
        "--sessions-dir",
        str(sessions_dir),
        "--max-mb",
        str(args.max_mb),
        "--target-mb",
        str(args.target_mb),
        "--backup-dir",
        str(today_dir),
    ]
    if args.dry_run:
        cmd.append("--dry-run")

    print("run:", " ".join(cmd))
    if not args.dry_run:
        today_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=False)

    # 2) Move any stray backups from sessions dir into archive
    moved = 0
    for p in iter_backup_files(sessions_dir):
        dest = today_dir / p.name
        print(f"move backup: {p.name} -> {dest}")
        if not args.dry_run:
            today_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(dest))
        moved += 1

    # 3) gzip backups in archive root
    gz = 0
    for p in archive_root.rglob("*.backup-*"):
        # Skip already gzipped via pattern
        if p.name.endswith(".gz"):
            continue
        print(f"gzip: {p}")
        if not args.dry_run:
            gzip_file(p)
        gz += 1

    # 4) Retention
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(args.keep_days))
    deleted = 0
    for p in archive_root.rglob("*.gz"):
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        except FileNotFoundError:
            continue
        if mtime < cutoff:
            print(f"delete(old): {p}")
            if not args.dry_run:
                p.unlink(missing_ok=True)
            deleted += 1

    # Remove empty date folders
    for d in sorted([x for x in archive_root.glob("*") if x.is_dir()]):
        try:
            if not any(d.iterdir()):
                print(f"rmdir(empty): {d}")
                if not args.dry_run:
                    d.rmdir()
        except Exception:
            pass

    print(f"OK: moved={moved} gzipped={gz} deleted_old={deleted}")


if __name__ == "__main__":
    main()
