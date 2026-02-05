#!/usr/bin/env python3

import argparse
import base64
from email.mime.text import MIMEText
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def build_message(to: str, subject: str, body: str, cc: str | None = None, bcc: str | None = None):
    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = to
    msg["subject"] = subject
    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return {"message": {"raw": raw}}


def main():
    ap = argparse.ArgumentParser(description="Create a Gmail Draft via Gmail API.")
    ap.add_argument("--account", required=True, help="Gmail address (informational; token determines actual account)")
    ap.add_argument("--config-dir", default=str(Path.home() / ".config" / "openclaw-gmail"))
    ap.add_argument("--token", default=None, help="Path to token.json (defaults to <config-dir>/token.json)")
    ap.add_argument("--to", required=True)
    ap.add_argument("--subject", required=True)
    body_group = ap.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body", help="Body text")
    body_group.add_argument("--body-file", help="Path to file containing body")
    ap.add_argument("--cc", default=None)
    ap.add_argument("--bcc", default=None)
    args = ap.parse_args()

    config_dir = Path(args.config_dir)
    token_path = Path(args.token) if args.token else (config_dir / "token.json")

    if not token_path.exists():
        raise SystemExit(f"Missing token.json at: {token_path}. Run auth.py first.")

    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    else:
        body = args.body

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    draft = build_message(args.to, args.subject, body, args.cc, args.bcc)
    result = service.users().drafts().create(userId="me", body=draft).execute()

    # result includes id + message.id
    draft_id = result.get("id")
    msg_id = (result.get("message") or {}).get("id")
    print(f"OK: draftId={draft_id} messageId={msg_id}")


if __name__ == "__main__":
    main()
