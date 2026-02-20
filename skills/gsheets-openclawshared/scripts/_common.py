from __future__ import annotations

from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

ALLOWED_FOLDER_ID = "1qlthNlyA1bxg-a4pMbC6MTrrXgd7tgV7"


def build_services(token_path: str | Path):
    token_path = Path(token_path).expanduser()
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    sheets = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return drive, sheets


def _iter_parents(drive, file_id: str):
    seen = set()
    cur = file_id
    while True:
        if cur in seen:
            break
        seen.add(cur)
        meta = drive.files().get(fileId=cur, fields="id, parents").execute()
        parents = meta.get("parents") or []
        if not parents:
            break
        for p in parents:
            yield p
        cur = parents[0]


def assert_in_allowed_folder(drive, file_id: str) -> None:
    if file_id == ALLOWED_FOLDER_ID:
        return
    for p in _iter_parents(drive, file_id):
        if p == ALLOWED_FOLDER_ID:
            return
    raise SystemExit(f"REFUSED: sheetId {file_id} is not under allowed folder {ALLOWED_FOLDER_ID} (OpenClawShared).")
