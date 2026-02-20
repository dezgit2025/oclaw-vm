#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

LIB_PATH = Path(__file__).resolve().parent / "food_library.json"
NUTR_DIR = Path("/home/desazure/.openclaw/workspace/nutrition")
SHEET_ID_PATH = NUTR_DIR / "sheet_id.txt"


def norm_name(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def load_library() -> dict[str, Any]:
    if not LIB_PATH.exists():
        return {"items": {}}
    return json.loads(LIB_PATH.read_text(encoding="utf-8"))


def resolve_library_item(lib: dict[str, Any], name: str):
    nn = norm_name(name)
    for key, item in (lib.get("items") or {}).items():
        names = [norm_name(n) for n in (item.get("names") or [])]
        if nn in names:
            return key, item
    return None, None


def add_nutrition(a: dict[str, float], b: dict[str, float], mul: float = 1.0) -> dict[str, float]:
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0.0) + (float(v or 0.0) * mul)
    return out


def compute_net_carbs(n: dict[str, float]) -> float:
    return max(float(n.get("carbs_g", 0.0)) - float(n.get("fiber_g", 0.0)), 0.0)


def load_day(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def day_totals(entries: list[dict[str, Any]]) -> dict[str, float]:
    total = {}
    for e in entries:
        n = (e.get("totals") or {})
        total = add_nutrition(total, n, 1.0)
    total["net_carbs_g"] = compute_net_carbs(total)
    return total


def sheet_timestamps_et():
    from zoneinfo import ZoneInfo

    ts_utc = datetime.now(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
    ts_et = datetime.now(ZoneInfo("America/New_York")).isoformat()
    date_et = ts_et.split("T", 1)[0]
    time_et = ts_et.split("T", 1)[1]
    return ts_utc, ts_et, date_et, time_et


def maybe_append_sheet_meal(date: str, title: str, totals: dict[str, float], ts_utc: str, ts_et: str, date_et: str, time_et: str, tag: str):
    """Append one row per meal into the Meals tab."""
    if not SHEET_ID_PATH.exists():
        return
    sheet_id = SHEET_ID_PATH.read_text(encoding="utf-8").strip()
    if not sheet_id:
        return

    token = str(Path.home() / ".config/openclaw-gdrive/token-sheets-openclawshared.json")
    script = "/home/desazure/.openclaw/workspace/skills/gsheets-openclawshared/scripts/append_row.py"
    py = "/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"

    row = [
        date,
        ts_utc,
        title,
        str(round(totals.get("calories_kcal", 0.0), 1)),
        str(round(totals.get("protein_g", 0.0), 1)),
        str(round(totals.get("carbs_g", 0.0), 1)),
        str(round(totals.get("fiber_g", 0.0), 1)),
        str(round(compute_net_carbs(totals), 1)),
        str(round(totals.get("fat_g", 0.0), 1)),
        str(round(totals.get("sugar_g", 0.0), 1)),
        str(round(totals.get("sodium_mg", 0.0), 1)),
        str(round(totals.get("alcohol_g", 0.0), 1)),
        str(round(totals.get("caffeine_mg", 0.0), 1)),
        ts_et,
        date_et,
        time_et,
        tag,
    ]

    import subprocess

    subprocess.run(
        [
            py,
            script,
            "--token",
            token,
            "--sheet-id",
            sheet_id,
            "--range",
            "Meals!A:Q",
            "--row",
            json.dumps(row),
        ],
        check=True,
    )


def maybe_append_sheet_items(date: str, title: str, items: list[dict[str, Any]], ts_utc: str, ts_et: str, date_et: str, time_et: str, tag: str):
    """Append one row per item into the Items tab."""
    if not SHEET_ID_PATH.exists():
        return
    sheet_id = SHEET_ID_PATH.read_text(encoding="utf-8").strip()
    if not sheet_id:
        return

    token = str(Path.home() / ".config/openclaw-gdrive/token-sheets-openclawshared.json")
    script = "/home/desazure/.openclaw/workspace/skills/gsheets-openclawshared/scripts/append_row.py"
    py = "/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"

    import subprocess

    for it in items:
        nutr = it.get("nutrition") or {}
        servings = float(it.get("servings", 1) or 1)
        item_totals = {k: float(v or 0.0) * servings for k, v in nutr.items()}

        row = [
            date,
            ts_utc,
            title,
            it.get("name", ""),
            str(servings),
            str(round(item_totals.get("calories_kcal", 0.0), 1)),
            str(round(item_totals.get("protein_g", 0.0), 1)),
            str(round(item_totals.get("carbs_g", 0.0), 1)),
            str(round(item_totals.get("fiber_g", 0.0), 1)),
            str(round(compute_net_carbs(item_totals), 1)),
            str(round(item_totals.get("fat_g", 0.0), 1)),
            str(round(item_totals.get("sugar_g", 0.0), 1)),
            str(round(item_totals.get("sodium_mg", 0.0), 1)),
            str(round(item_totals.get("alcohol_g", 0.0), 1)),
            str(round(item_totals.get("caffeine_mg", 0.0), 1)),
            ts_et,
            date_et,
            time_et,
            tag,
        ]

        subprocess.run(
            [
                py,
                script,
                "--token",
                token,
                "--sheet-id",
                sheet_id,
                "--range",
                "Items!A:S",
                "--row",
                json.dumps(row),
            ],
            check=True,
        )


def main():
    ap = argparse.ArgumentParser(description="Log a meal + compute daily totals")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--title", default="Meal")
    ap.add_argument("--items-json", required=True, help="JSON list of items. Each item: {name, servings?}")
    ap.add_argument("--notes", default="")
    ap.add_argument("--tag", default="real", help="Row tag: real|test|template (stored in Sheets)")
    args = ap.parse_args()

    NUTR_DIR.mkdir(parents=True, exist_ok=True)
    day_path = NUTR_DIR / f"{args.date}.jsonl"

    lib = load_library()
    items_in = json.loads(args.items_json)

    resolved_items = []
    meal_totals: dict[str, float] = {}

    for it in items_in:
        name = it.get("name") or ""
        servings = float(it.get("servings", 1) or 1)
        key, li = resolve_library_item(lib, name)
        if li is None:
            # If no exact match, require caller to supply nutrition explicitly.
            nutr = it.get("nutrition")
            if not nutr:
                raise SystemExit(f"Missing nutrition for unknown item: {name}. Add it to library or include nutrition in items-json.")
            # Allow optional fields (e.g., cholesterol_mg) to be omitted (blank/unknown).
            nutr = {k: float(v) for k, v in nutr.items() if v is not None}
            resolved_items.append({"name": name, "servings": servings, "nutrition": nutr, "source": "manual"})
            meal_totals = add_nutrition(meal_totals, nutr, servings)
        else:
            nutr = li.get("nutrition") or {}
            # If library entry has nulls, fail fast to avoid silent wrong totals.
            if any(nutr.get(k) is None for k in ["calories_kcal", "protein_g", "carbs_g", "fat_g"]):
                raise SystemExit(f"Library item '{name}' exists but has incomplete nutrition. Fill it in via add_food.py.")
            # Allow optional fields (e.g., cholesterol_mg) to be omitted (blank/unknown).
            nutr = {k: float(v) for k, v in nutr.items() if v is not None}
            resolved_items.append({"name": name, "key": key, "servings": servings, "nutrition": nutr, "source": "library"})
            meal_totals = add_nutrition(meal_totals, nutr, servings)

    meal_totals["net_carbs_g"] = compute_net_carbs(meal_totals)

    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "date": args.date,
        "title": args.title,
        "items": resolved_items,
        "totals": meal_totals,
        "notes": args.notes,
    }

    with open(day_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

    entries = load_day(day_path)
    totals = day_totals(entries)

    # Optional Sheets append
    try:
        ts_utc, ts_et, date_et, time_et = sheet_timestamps_et()
        maybe_append_sheet_meal(args.date, args.title, meal_totals, ts_utc, ts_et, date_et, time_et, args.tag)
        maybe_append_sheet_items(args.date, args.title, resolved_items, ts_utc, ts_et, date_et, time_et, args.tag)
    except Exception as e:
        print(f"WARN: sheets append failed: {e}")

    print("OK: logged", day_path)
    print(json.dumps({"meal_totals": meal_totals, "day_totals": totals}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
