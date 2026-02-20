#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Read/write Drive scope (cannot be limited to a folder by Google; we enforce folder-only in code)
SCOPES = ["https://www.googleapis.com/auth/drive"]


def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def main():
    ap = argparse.ArgumentParser(description="OAuth auth for Google Drive (Drive API).")
    ap.add_argument("--account", required=True)
    ap.add_argument(
        "--config-dir",
        default=str(Path.home() / ".config" / "openclaw-gdrive"),
        help="Directory containing credentials.json",
    )
    ap.add_argument("--creds", default=None, help="Path to credentials.json (defaults to <config-dir>/credentials.json)")
    ap.add_argument("--token", required=True, help="Path to write token.json")
    ap.add_argument("--port", type=int, default=18794, help="Local server port for OAuth redirect (tunnel flow)")
    ap.add_argument("--no-local-server", action="store_true", help="Use console flow (headless VMs)")
    ap.add_argument("--print-url-only", action="store_true", help="Print URL then exit (for testing)")
    args = ap.parse_args()

    config_dir = Path(args.config_dir)
    creds_path = Path(args.creds) if args.creds else (config_dir / "credentials.json")
    token_path = Path(args.token).expanduser()

    if not creds_path.exists():
        raise SystemExit(
            f"Missing credentials.json at: {creds_path}. "
            "Copy your Google OAuth client JSON here (Desktop app client)."
        )

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        info = json.loads(creds_path.read_text(encoding="utf-8"))
        flow = InstalledAppFlow.from_client_config(info, SCOPES)

        if args.no_local_server:
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
            creds = flow.credentials
        else:
            creds = flow.run_local_server(host="127.0.0.1", port=args.port, open_browser=False)

    ensure_parent(token_path)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    print(f"OK: account={args.account} wrote token to {token_path}")


if __name__ == "__main__":
    main()
