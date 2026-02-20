#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Minimal send scope
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def main():
    ap = argparse.ArgumentParser(description="OAuth auth for Gmail alerts (gmail.send scope).")
    ap.add_argument("--account", required=True, help="Gmail address (informational; token determines actual account)")
    ap.add_argument(
        "--config-dir",
        default=str(Path.home() / ".config" / "openclaw-gmail"),
        help="Directory containing credentials.json",
    )
    ap.add_argument("--creds", default=None, help="Path to credentials.json (defaults to <config-dir>/credentials.json)")
    ap.add_argument("--token", required=True, help="Path to write the alerts token.json (e.g. ~/.config/openclaw-gmail/token-alerts.json)")
    ap.add_argument(
        "--no-local-server",
        action="store_true",
        help=(
            "(deprecated) Use console flow. Google often blocks OOB/console flows; prefer the local-server flow with an SSH tunnel."
        ),
    )
    ap.add_argument("--port", type=int, default=18793, help="Local server port for OAuth redirect (default: 18793)")
    args = ap.parse_args()

    config_dir = Path(args.config_dir)
    creds_path = Path(args.creds) if args.creds else (config_dir / "credentials.json")
    token_path = Path(args.token).expanduser()

    if not creds_path.exists():
        raise SystemExit(f"Missing credentials.json at: {creds_path}")

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
            code = input("Code: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials
        else:
            # Headless-friendly: don't try to open a browser on the server.
            # Users can use an SSH tunnel to reach this localhost callback.
            creds = flow.run_local_server(host="127.0.0.1", port=args.port, open_browser=False)

    ensure_parent(token_path)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    print(f"OK: wrote alerts token to {token_path}")


if __name__ == "__main__":
    main()
