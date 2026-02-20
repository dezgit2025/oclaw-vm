#!/usr/bin/env python3

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def mtime_dt(p: Path) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
    except FileNotFoundError:
        return None


def load_json(p: Path) -> Optional[dict]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


@dataclass
class TokenCheck:
    name: str
    path: Path
    scopes_hint: str


def summarize_creds(creds_path: Path) -> dict:
    d = load_json(creds_path) or {}
    # Google OAuth desktop client JSON often has "installed" key.
    root = d.get("installed") or d.get("web") or {}
    return {
        "project_id": root.get("project_id"),
        "client_id": root.get("client_id"),
        "auth_uri": root.get("auth_uri"),
        "token_uri": root.get("token_uri"),
    }


def summarize_token(token_path: Path) -> dict:
    d = load_json(token_path) or {}
    return {
        "has_refresh_token": bool(d.get("refresh_token")),
        "expiry": d.get("expiry"),
        "scopes": d.get("scopes"),
        "token_type": d.get("token_type"),
    }


def main():
    home = Path.home()

    configs = {
        "gmail": {
            "config_dir": home / ".config/openclaw-gmail",
            "creds": home / ".config/openclaw-gmail/credentials.json",
            "tokens": [
                home / ".config/openclaw-gmail/token-assistantdesi_gmail_com.json",
                home / ".config/openclaw-gmail/token-desi4k_gmail_com.json",
                home / ".config/openclaw-gmail/token.json",
            ],
        },
        "gdrive": {
            "config_dir": home / ".config/openclaw-gdrive",
            "creds": home / ".config/openclaw-gdrive/credentials.json",
            "tokens": [
                home / ".config/openclaw-gdrive/token-openclawshared.json",
                home / ".config/openclaw-gdrive/token-docs-openclawshared.json",
                home / ".config/openclaw-gdrive/token-sheets-openclawshared.json",
            ],
        },
        "gcal": {
            "config_dir": home / ".config/openclaw-gcal",
            "creds": home / ".config/openclaw-gcal/credentials.json",
            "tokens": [
                home / ".config/openclaw-gcal/token-readonly.json",
                home / ".config/openclaw-gcal/token-write.json",
            ],
        },
    }

    now = utc_now()
    print(f"# Google OAuth audit (local)\n")
    print(f"Generated: {now.isoformat()}\n")

    # 1) Credential client churn risk
    print("## Credential files (client IDs / project IDs)\n")
    seen_client_ids = {}
    for k, cfg in configs.items():
        creds_path: Path = cfg["creds"]
        if not creds_path.exists():
            print(f"- {k}: MISSING creds: {creds_path}")
            continue
        s = summarize_creds(creds_path)
        client_id = s.get("client_id")
        project_id = s.get("project_id")
        mt = mtime_dt(creds_path)
        print(f"- {k}: creds={creds_path} mtime={mt.isoformat() if mt else None}")
        print(f"  - project_id: {project_id}")
        print(f"  - client_id:  {client_id}")
        if client_id:
            seen_client_ids.setdefault(client_id, []).append(k)

    if len(seen_client_ids) > 1:
        print("\n⚠️  Multiple OAuth client_ids detected across APIs. This increases fragility (more places to re-auth).")

    # 2) Token health
    print("\n## Token files (refresh token presence + age)\n")
    for k, cfg in configs.items():
        print(f"### {k}")
        for token_path in cfg["tokens"]:
            if not token_path.exists():
                print(f"- MISSING: {token_path}")
                continue
            mt = mtime_dt(token_path)
            age_days = (now - mt).total_seconds() / 86400 if mt else None
            t = summarize_token(token_path)
            print(f"- {token_path} mtime={mt.isoformat() if mt else None} age_days={age_days:.1f}")
            print(f"  - has_refresh_token: {t['has_refresh_token']}")
            if not t["has_refresh_token"]:
                print("  ⚠️  No refresh token. This will force frequent re-auth.")

    print("\n## What we *cannot* audit locally\n")
    print("- Whether your OAuth Consent Screen is in TESTING vs PRODUCTION")
    print("- Whether scopes triggered verification requirements")
    print("- Whether Google flagged the app as risky or revoked tokens")

    print("\n## Recommendations (consumer Gmail)\n")
    print("1) Ensure every auth uses offline access + consent so refresh_token is present.")
    print("2) Put consent screen in PRODUCTION where possible.")
    print("3) Avoid deleting/recreating OAuth clients; reuse the same client_id.")
    print("4) Keep per-capability tokens (gmail vs drive vs cal) and per-account tokens.")


if __name__ == "__main__":
    main()
