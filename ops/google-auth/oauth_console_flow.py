#!/usr/bin/env python3

import json
from dataclasses import dataclass
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


@dataclass
class ConsoleOAuthArgs:
    creds_path: Path
    token_path: Path
    scopes: list[str]
    print_url_only: bool = False


def run_console_oauth(args: ConsoleOAuthArgs) -> Credentials:
    if not args.creds_path.exists():
        raise SystemExit(f"Missing credentials.json at: {args.creds_path}")

    creds = None
    if args.token_path.exists():
        creds = Credentials.from_authorized_user_file(str(args.token_path), args.scopes)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        return creds

    if creds and creds.valid:
        return creds

    info = json.loads(args.creds_path.read_text(encoding="utf-8"))
    flow = InstalledAppFlow.from_client_config(info, args.scopes)

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    print("Open this URL in a browser, approve, then paste the code here:\n")
    print(auth_url)
    print("")

    if args.print_url_only:
        raise SystemExit("PRINT_URL_ONLY")

    code = input("Code: ").strip()
    flow.fetch_token(code=code)
    return flow.credentials
