from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]

# Hard-restrict everything to this folder (OpenClawShared)
ALLOWED_FOLDER_ID = "1qlthNlyA1bxg-a4pMbC6MTrrXgd7tgV7"


@dataclass
class DriveClient:
    service: object


def build_drive(token_path: str | Path) -> DriveClient:
    token_path = Path(token_path).expanduser()
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return DriveClient(service=service)


def _iter_parents(service, file_id: str) -> Iterable[str]:
    # Walk up parents until root; yields parent ids.
    seen = set()
    cur = file_id
    while True:
        if cur in seen:
            break
        seen.add(cur)
        meta = service.files().get(fileId=cur, fields="id, parents").execute()
        parents = meta.get("parents") or []
        if not parents:
            break
        for p in parents:
            yield p
        # pick first parent for climb (Drive can have multiple parents historically)
        cur = parents[0]


def assert_in_allowed_folder(service, file_id: str) -> None:
    if file_id == ALLOWED_FOLDER_ID:
        return
    for p in _iter_parents(service, file_id):
        if p == ALLOWED_FOLDER_ID:
            return
    raise SystemExit(
        f"REFUSED: fileId {file_id} is not under allowed folder {ALLOWED_FOLDER_ID} (OpenClawShared)."
    )
