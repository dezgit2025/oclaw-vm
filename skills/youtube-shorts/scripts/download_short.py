#!/usr/bin/env python3
"""Download a YouTube Short via yt-dlp, optionally upload to Drive and/or attach to a Gmail draft.

Design goals:
- cookie-free by default
- deterministic outputs + logs
- best-effort integrations (Drive token may be invalid; keep local file)

This script is intended to be called via download_short.sh.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def safe_slug(s: str) -> str:
    s = s.strip()
    s = re.sub(r"https?://", "", s)
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return (s[:80] or "short").lower()


def run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=check)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out-dir", default=str(Path("/home/desazure/.openclaw/workspace/youtube/shorts/out")))
    ap.add_argument("--upload-drive", action="store_true")

    # Gmail draft options
    ap.add_argument(
        "--gmail-draft",
        action="store_true",
        help="Create a Gmail draft (defaults to --gmail-default-to if --gmail-draft-to not set)",
    )
    ap.add_argument("--gmail-draft-to", default="", help="Recipient for Gmail draft")
    ap.add_argument("--gmail-default-to", default="desi4k@gmail.com", help="Default recipient when using --gmail-draft")
    ap.add_argument("--gmail-account", default="assistantdesi@gmail.com")

    ap.add_argument("--title", default="YouTube Short")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = utc_stamp()
    slug = safe_slug(args.url)

    # Use yt-dlp template with %(id)s when possible; fallback to slug.
    base = out_dir / f"{slug}-{stamp}"
    out_tpl = str(base) + "-%(id)s.%(ext)s"

    ytdlp_cmd = [
        "yt-dlp",
        "--no-playlist",
        "--restrict-filenames",
        "-f",
        "bv*+ba/b",
        "--merge-output-format",
        "mp4",
        "-o",
        out_tpl,
        args.url,
    ]

    log_path = Path(str(base) + ".ytdl.log.txt")

    print("OUT_DIR:", out_dir)
    print("LOG:", log_path)
    print("CMD:", " ".join(shlex.quote(x) for x in ytdlp_cmd))

    if args.dry_run:
        print("DRY_RUN: skipping download")
        return

    res = run(ytdlp_cmd, check=False)
    log_path.write_text(res.stdout, encoding="utf-8", errors="replace")

    if res.returncode != 0:
        print("ERROR: yt-dlp failed; see log:", log_path)
        raise SystemExit(res.returncode)

    # Find newest mp4 produced by this run.
    mp4s = sorted(out_dir.glob(f"{slug}-{stamp}-*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not mp4s:
        # Sometimes yt-dlp chooses .mkv and then remuxes; but we force mp4.
        # Still, be defensive.
        mp4s = sorted(out_dir.glob(f"{slug}-{stamp}-*"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not mp4s:
        print("WARN: download succeeded but could not find output file; check log:", log_path)
        return

    out_file = mp4s[0]
    print("OK: downloaded:", out_file)

    # Optional Drive upload
    if args.upload_drive:
        token = str(Path.home() / ".config/openclaw-gdrive/token-openclawshared.json")
        uploader = "/home/desazure/.openclaw/workspace/skills/gdrive-openclawshared/scripts/upload_file.py"
        py = "/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"
        cmd = [py, uploader, "--token", token, "--path", str(out_file)]
        print("Drive upload:", " ".join(shlex.quote(x) for x in cmd))
        up = run(cmd, check=False)
        drive_log = Path(str(base) + ".drive-upload.log.txt")
        drive_log.write_text(up.stdout, encoding="utf-8", errors="replace")
        if up.returncode == 0:
            print("OK: uploaded to Drive (see output above)")
        else:
            print("WARN: Drive upload failed (kept local file). See:", drive_log)

    # Optional Gmail draft with attachment
    gmail_to = ""
    if args.gmail_draft_to:
        gmail_to = args.gmail_draft_to
    elif args.gmail_draft:
        gmail_to = args.gmail_default_to

    if gmail_to:
        drafter = "/home/desazure/.openclaw/workspace/skills/gmail-drafts/scripts/create_draft.py"
        py = "/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"
        cmd = [
            py,
            drafter,
            "--account",
            args.gmail_account,
            "--to",
            gmail_to,
            "--subject",
            args.title,
            "--body",
            f"Attached: {out_file.name}",
            "--attach-file",
            str(out_file),
        ]
        print("Gmail draft:", " ".join(shlex.quote(x) for x in cmd))
        dr = run(cmd, check=False)
        gmail_log = Path(str(base) + ".gmail-draft.log.txt")
        gmail_log.write_text(dr.stdout, encoding="utf-8", errors="replace")
        if dr.returncode == 0:
            print("OK: created Gmail draft (see output above)")
        else:
            print("WARN: Gmail draft failed (kept local file). See:", gmail_log)


if __name__ == "__main__":
    main()
