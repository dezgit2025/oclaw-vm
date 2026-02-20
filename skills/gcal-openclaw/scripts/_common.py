from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


@dataclass
class Services:
    cal: object


def build_calendar(token_path: str | Path, scopes: list[str]) -> Services:
    token_path = Path(token_path).expanduser()
    creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    cal = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return Services(cal=cal)


def load_creds_json(creds_path: Path) -> dict:
    return json.loads(creds_path.read_text(encoding="utf-8"))
