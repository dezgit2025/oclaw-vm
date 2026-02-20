#!/usr/bin/env python3

import argparse
import base64
import re
from email.mime.text import MIMEText
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Hard safety rails
FIXED_TO = "desi4k@gmail.com"
SUBJECT_PREFIX = "[OpenClaw ALERT] "
MAX_SUBJECT_LEN = 160
MAX_BODY_LEN = 8000


def _clean_subject(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    if not s:
        s = "Alert"
    s = s[:MAX_SUBJECT_LEN]
    return SUBJECT_PREFIX + s


def _clean_body(s: str) -> str:
    # Plain text only; normalize line endings
    s = (s or "").replace("\r\n", "\n").replace("\r", "\n")
    s = s.strip()
    if not s:
        s = "(no details)"
    return s[:MAX_BODY_LEN]


def build_raw_message(subject: str, body: str) -> dict:
    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = FIXED_TO
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return {"raw": raw}


def main():
    ap = argparse.ArgumentParser(description="Send a restricted alert email via Gmail API (to fixed recipient only).")
    ap.add_argument("--config-dir", default=str(Path.home() / ".config" / "openclaw-gmail"))
    ap.add_argument("--token", required=True, help="Path to alerts token.json (gmail.send scope)")
    ap.add_argument("--subject", required=True, help="Short subject (prefix added automatically)")
    body_group = ap.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body", help="Body text")
    body_group.add_argument("--body-file", help="Path to file containing body")
    args = ap.parse_args()

    token_path = Path(args.token).expanduser()
    if not token_path.exists():
        raise SystemExit(f"Missing token at: {token_path}. Run auth_alerts.py first.")

    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    else:
        body = args.body

    subject = _clean_subject(args.subject)
    body = _clean_body(body)

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    result = service.users().messages().send(userId="me", body=build_raw_message(subject, body)).execute()
    msg_id = result.get("id")
    thread_id = result.get("threadId")
    print(f"OK: sent messageId={msg_id} threadId={thread_id} to={FIXED_TO}")


if __name__ == "__main__":
    main()
