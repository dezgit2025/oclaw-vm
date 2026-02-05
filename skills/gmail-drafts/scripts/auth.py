#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def main():
    ap = argparse.ArgumentParser(description="OAuth auth for Gmail draft creation (gmail.compose scope).")
    ap.add_argument("--account", required=True, help="Gmail address (for naming token file).")
    ap.add_argument(
        "--config-dir",
        default=str(Path.home() / ".config" / "openclaw-gmail"),
        help="Directory containing credentials.json and where token.json is stored",
    )
    ap.add_argument(
        "--creds",
        default=None,
        help="Path to credentials.json (defaults to <config-dir>/credentials.json)",
    )
    ap.add_argument(
        "--token",
        default=None,
        help="Path to token.json (defaults to <config-dir>/token.json)",
    )
    ap.add_argument("--no-local-server", action="store_true", help="Use console flow (for headless servers)")
    args = ap.parse_args()

    config_dir = Path(args.config_dir)
    creds_path = Path(args.creds) if args.creds else (config_dir / "credentials.json")
    token_path = Path(args.token) if args.token else (config_dir / "token.json")

    if not creds_path.exists():
        raise SystemExit(f"Missing credentials.json at: {creds_path}")

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        with open(creds_path, "r", encoding="utf-8") as f:
            info = json.load(f)

        flow = InstalledAppFlow.from_client_config(info, SCOPES)

        if args.no_local_server:
            # Headless-friendly flow: print auth URL, user pastes code.
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
            )
            print("Open this URL in a browser, approve, then paste the code here:\n")
            print(auth_url)
            print("")
            code = input("Code: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials
        else:
            creds = flow.run_local_server(port=0)

    ensure_parent(token_path)
    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"OK: wrote token to {token_path}")


if __name__ == "__main__":
    main()
