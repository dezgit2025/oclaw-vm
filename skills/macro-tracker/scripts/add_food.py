#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path

LIB_PATH = Path(__file__).resolve().parent / "food_library.json"


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "item"


def main():
    ap = argparse.ArgumentParser(description="Add/update an exact/common food item in the macro-tracker library")
    ap.add_argument("--name", required=True, help="Canonical display name")
    ap.add_argument("--key", default=None, help="Optional library key (slug). Defaults to slug(name)")
    ap.add_argument("--alias", action="append", default=[], help="Additional alias name (repeatable)")
    ap.add_argument("--serving", required=True, help="Serving description, e.g. '1 sandwich' or 'grande (16 oz)'")

    # nutrition
    ap.add_argument("--calories", type=float, required=True)
    ap.add_argument("--protein", type=float, required=True)
    ap.add_argument("--carbs", type=float, required=True)
    ap.add_argument("--fat", type=float, required=True)

    ap.add_argument("--fiber", type=float, default=0)
    ap.add_argument("--sugar", type=float, default=0)
    ap.add_argument("--sodium", type=float, default=0, help="mg")
    ap.add_argument("--cholesterol", type=float, default=None, help="mg (optional; omit if unknown)")
    ap.add_argument("--alcohol", type=float, default=0, help="g")
    ap.add_argument("--caffeine", type=float, default=0, help="mg")

    args = ap.parse_args()

    key = args.key or slugify(args.name)
    data = json.loads(LIB_PATH.read_text(encoding="utf-8")) if LIB_PATH.exists() else {"version": 1, "items": {}}
    items = data.setdefault("items", {})

    names = [args.name] + (args.alias or [])
    names_norm = sorted({n.strip().lower() for n in names if n.strip()})

    items[key] = {
        "names": names_norm,
        "serving": args.serving,
        "nutrition": {
            "calories_kcal": args.calories,
            "protein_g": args.protein,
            "carbs_g": args.carbs,
            "fat_g": args.fat,
            "fiber_g": args.fiber,
            "sugar_g": args.sugar,
            "sodium_mg": args.sodium,
            **({"cholesterol_mg": args.cholesterol} if args.cholesterol is not None else {}),
            "alcohol_g": args.alcohol,
            "caffeine_mg": args.caffeine,
        },
        "notes": "exact",
    }

    LIB_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"OK: upserted key={key} names={names_norm} library={LIB_PATH}")


if __name__ == "__main__":
    main()
