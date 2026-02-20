#!/usr/bin/env python3
"""Clean up gateway watchdog logs.

Two behaviors:
1) Retention: delete daily log files older than N days (default: keep 2 days).
2) Optional compaction: archive today's log and start a fresh file containing only
   the last K lines (default: 300). This is useful when a log got spammy.

Designed to be safe to run from cron; does not require systemd/DBus.

Exit codes:
- 0 success
- 2 nothing to do
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
from pathlib import Path


def utc_today_str() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def parse_ymd(name: str) -> dt.date | None:
    try:
        return dt.datetime.strptime(name, "%Y-%m-%d").date()
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--log-dir",
        default=os.path.expanduser("~/.openclaw/logs/gateway-watchdog"),
        help="Directory containing YYYY-MM-DD.log files",
    )
    ap.add_argument(
        "--keep-days",
        type=int,
        default=2,
        help="Keep this many days of .log files (older will be deleted)",
    )
    ap.add_argument(
        "--compact-today",
        action="store_true",
        help="Archive today's log and keep only the last --tail-lines lines",
    )
    ap.add_argument(
        "--tail-lines",
        type=int,
        default=300,
        help="Lines to keep when compacting today's log",
    )
    args = ap.parse_args()

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    today = dt.datetime.now(dt.timezone.utc).date()

    # 1) Retention
    deleted: list[Path] = []
    for p in sorted(log_dir.glob("*.log")):
        d = parse_ymd(p.stem)
        if d is None:
            continue
        age_days = (today - d).days
        if age_days > args.keep_days:
            try:
                p.unlink()
                deleted.append(p)
            except FileNotFoundError:
                pass

    # 2) Optional compaction
    compacted = False
    archived_path: Path | None = None
    if args.compact_today:
        today_log = log_dir / f"{utc_today_str()}.log"
        if today_log.exists() and today_log.stat().st_size > 0:
            ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            archived_path = log_dir / f"{today_log.stem}.log.bak-{ts}"
            # Read last K lines
            with today_log.open("r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            tail = lines[-args.tail_lines :] if args.tail_lines > 0 else []

            # Archive original
            shutil.move(str(today_log), str(archived_path))

            # Write new compacted file
            header = [
                "---\n",
                f"[{ts}] clean_watchdog_logs.py compacted today's log; archived to {archived_path.name}; kept last {len(tail)} lines\n",
            ]
            with today_log.open("w", encoding="utf-8") as f:
                f.writelines(header)
                f.writelines(tail)
            compacted = True

    # Output summary
    ts_out = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts_out}] keep_days={args.keep_days} deleted_files={len(deleted)} compacted_today={int(compacted)}")
    if deleted:
        for p in deleted:
            print(f"deleted: {p.name}")
    if archived_path is not None:
        print(f"archived_today: {archived_path.name}")

    if not deleted and not compacted:
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
