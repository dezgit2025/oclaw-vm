#!/usr/bin/env python3

"""One-off checker for ShoppingWatchlist.

- Reads Watchlist tab rows.
- For active rows with URL, fetches HTML and extracts a best-effort price.
- Writes last_price, last_checked_et, status back to the sheet.

Heuristics only (Phase I). Some retailers may require browser fallback.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from urllib.request import Request, urlopen

from zoneinfo import ZoneInfo

# Use our existing Sheets client helper
sys.path.insert(0, "/home/desazure/.openclaw/workspace/skills/gsheets-openclawshared/scripts")
from _common import build_services  # type: ignore


def now_et_iso():
    return datetime.now(ZoneInfo("America/New_York")).isoformat()


def fetch_html(url: str, timeout: int = 25) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        method="GET",
    )
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    # best-effort decode
    for enc in ("utf-8", "latin-1"):
        try:
            return data.decode(enc, errors="ignore")
        except Exception:
            pass
    return data.decode("utf-8", errors="ignore")


def extract_price(html: str) -> float | None:
    # 1) JSON-LD priceCurrency/price pairs
    m = re.search(r"\"price\"\s*:\s*\"?([0-9]+(?:\.[0-9]{1,2})?)\"?", html)
    if m:
        try:
            v = float(m.group(1))
            if 0 < v < 10000:
                return v
        except Exception:
            pass

    # 2) Common meta tags
    m = re.search(r"property=\"product:price:amount\"[^>]*content=\"([0-9]+(?:\.[0-9]{1,2})?)\"", html)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            pass

    # 3) Fallback: first reasonable $ number
    m = re.search(r"\$\s*([0-9]{1,4}(?:\.[0-9]{2})?)", html)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            pass

    return None


def main():
    sheet_id = os.environ.get("SHOPPING_SHEET_ID")
    token = os.environ.get("SHEETS_TOKEN")
    if not sheet_id or not token:
        raise SystemExit("Need env SHOPPING_SHEET_ID and SHEETS_TOKEN")

    drive, sheets = build_services(token)

    # Read Watchlist rows (A:L)
    resp = sheets.spreadsheets().values().get(spreadsheetId=sheet_id, range="Watchlist!A2:L").execute()
    rows = resp.get("values") or []

    updates = []  # list of (row_index_1based, last_price, last_checked_et, status)

    for i, r in enumerate(rows, start=2):
        active = (r[0].strip().lower() if len(r) > 0 else "")
        url = (r[2].strip() if len(r) > 2 else "")
        if active not in ("true", "yes", "1"):
            continue
        if not url:
            continue
        try:
            html = fetch_html(url)
            price = extract_price(html)
            if price is None:
                updates.append((i, "", now_et_iso(), "no_price_found"))
            else:
                updates.append((i, str(price), now_et_iso(), "ok"))
        except Exception as e:
            updates.append((i, "", now_et_iso(), f"error:{type(e).__name__}"))

    if not updates:
        print("OK: nothing to update")
        return

    # Write back columns: last_price (G), last_checked_et (I), status (J)
    for row_i, last_price, last_checked_et, status in updates:
        rng = f"Watchlist!G{row_i}:J{row_i}"
        values = [[last_price, "USD", last_checked_et, status]]
        sheets.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=rng,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()
        print(f"OK: updated row {row_i} price={last_price} status={status}")


if __name__ == "__main__":
    main()
