#!/usr/bin/env python3
"""OpenClaw session log GC.

Goal:
- If any session .jsonl file exceeds MAX_MB, back it up
- Truncate oldest *message* entries so the file shrinks to TARGET_MB
- Preserve the non-message header lines at the top of the session file

This is a pragmatic safety valve for context-overflow incidents.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple


@dataclass
class Result:
    path: Path
    original_bytes: int
    backup_path: Path | None
    new_bytes: int | None
    truncated: bool
    reason: str


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def read_lines(p: Path) -> List[str]:
    # Keep raw lines (including trailing \n) for exact byte accounting.
    return p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)


def split_header_and_body(lines: List[str]) -> Tuple[List[str], List[str]]:
    """Split into header (non-message event lines at the start) and body (everything after).

    We treat the first contiguous block of non-"message" types as header.
    If parsing fails for a line, we assume it's body.
    """

    header: List[str] = []
    body: List[str] = []

    in_body = False
    for ln in lines:
        if in_body:
            body.append(ln)
            continue
        try:
            obj = json.loads(ln)
            t = obj.get("type")
        except Exception:
            t = None
        if t == "message":
            in_body = True
            body.append(ln)
        else:
            header.append(ln)

    return header, body


def tail_to_fit(header: List[str], body: List[str], target_bytes: int) -> List[str]:
    hb = sum(len(x.encode("utf-8", errors="replace")) for x in header)
    if hb >= target_bytes:
        # Header alone exceeds target; keep header only (best effort).
        return header

    remaining = target_bytes - hb

    out_body: List[str] = []
    acc = 0
    # Take from the end until we reach remaining bytes.
    for ln in reversed(body):
        b = len(ln.encode("utf-8", errors="replace"))
        if acc + b > remaining and out_body:
            break
        if b > remaining and not out_body:
            # Single gigantic line; keep it (can't do better without partial-line surgery).
            out_body.append(ln)
            acc += b
            break
        out_body.append(ln)
        acc += b

    out_body.reverse()
    return header + out_body


def process_file(p: Path, max_bytes: int, target_bytes: int, backup_dir: Path | None) -> Result:
    try:
        original_bytes = p.stat().st_size
    except FileNotFoundError:
        return Result(p, 0, None, None, False, "missing")

    if original_bytes <= max_bytes:
        return Result(p, original_bytes, None, None, False, "below-threshold")

    lines = read_lines(p)
    header, body = split_header_and_body(lines)
    new_lines = tail_to_fit(header, body, target_bytes)
    new_text = "".join(new_lines)
    new_bytes = len(new_text.encode("utf-8", errors="replace"))

    stamp = utc_stamp()
    backup_path = None

    if backup_dir is not None:
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{p.name}.backup-{stamp}"
    else:
        backup_path = p.with_name(f"{p.name}.backup-{stamp}")

    # Backup then atomic replace
    p.replace(backup_path)

    tmp_path = p.with_suffix(p.suffix + ".tmp")
    tmp_path.write_text(new_text, encoding="utf-8")
    os.replace(tmp_path, p)

    return Result(p, original_bytes, backup_path, new_bytes, True, "truncated")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--sessions-dir",
        default=str(Path.home() / ".openclaw" / "agents" / "main" / "sessions"),
        help="Directory containing session .jsonl files",
    )
    ap.add_argument("--max-mb", type=float, default=5.0)
    ap.add_argument("--target-mb", type=float, default=3.0)
    ap.add_argument(
        "--backup-dir",
        default="",
        help="Optional directory to store backups (default: alongside original file)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sessions_dir = Path(args.sessions_dir).expanduser()
    max_bytes = int(args.max_mb * 1024 * 1024)
    target_bytes = int(args.target_mb * 1024 * 1024)

    backup_dir = Path(args.backup_dir).expanduser() if args.backup_dir else None

    if not sessions_dir.exists():
        print(f"No sessions dir: {sessions_dir}")
        raise SystemExit(2)

    files = sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    results: List[Result] = []

    for p in files:
        sz = p.stat().st_size
        if sz <= max_bytes:
            continue

        if args.dry_run:
            results.append(Result(p, sz, None, None, False, "would-truncate"))
            continue

        results.append(process_file(p, max_bytes=max_bytes, target_bytes=target_bytes, backup_dir=backup_dir))

    if not results:
        print("OK: no session files exceeded threshold")
        return

    for r in results:
        if args.dry_run:
            print(f"DRY_RUN: {r.path} is {r.original_bytes} bytes > {max_bytes}")
        else:
            print(
                f"TRUNCATED: {r.path} {r.original_bytes} -> {r.new_bytes} bytes (backup: {r.backup_path})"
            )


if __name__ == "__main__":
    main()
