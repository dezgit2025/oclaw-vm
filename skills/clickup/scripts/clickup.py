#!/usr/bin/env python3

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests


def load_token(token_file: Optional[str] = None) -> str:
    p = Path(token_file) if token_file else (Path.home() / ".config" / "openclaw-clickup" / "token")
    token = p.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError(f"Empty token file: {p}")
    return token


def client(token: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Authorization": token, "Content-Type": "application/json"})
    return s


def api_get(s: requests.Session, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = f"https://api.clickup.com/api/v2{path}"
    r = s.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def api_post(s: requests.Session, path: str, body: Dict[str, Any]) -> Any:
    url = f"https://api.clickup.com/api/v2{path}"
    r = s.post(url, data=json.dumps(body), timeout=30)
    r.raise_for_status()
    return r.json()
