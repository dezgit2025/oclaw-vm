---
name: macro-tracker
description: Track daily calories/macros/fiber/sugar/sodium/alcohol/caffeine from food photos + short descriptions; log meals locally and (optionally) append rows to a Google Sheet in OpenClawShared.
user-invocable: true
---

# Macro Tracker (photo + description → daily totals)

Use this skill when the user wants to log a meal/snack/drink and keep daily totals for:
- calories
- protein / carbs (total + net) / fat
- fiber, sugar, sodium
- alcohol
- caffeine

## Core workflow
1) User sends a **photo** + optional text.
2) You identify foods + estimate portions.
3) If the user names a known item (e.g., **Starbucks grilled cheese**), prefer the **exact entry** from the food library.
4) Produce a structured entry and log it via `scripts/log_meal.py`.
5) Show updated day totals.

## Data model
A meal is a list of items. Each item should include:
- name
- quantity + unit (optional but preferred)
- nutrition per item (or per serving), with fields:
  - calories_kcal
  - protein_g, carbs_g, fat_g
  - fiber_g, sugar_g
  - sodium_mg
  - alcohol_g
  - caffeine_mg

Net carbs are computed as:
- `net_carbs_g = max(carbs_g - fiber_g, 0)`

## Food library (exact/common items)
- Library file: `scripts/food_library.json`
- Add/update an exact item (e.g., Starbucks menu items) using:

```bash
python3 /home/desazure/.openclaw/workspace/skills/macro-tracker/scripts/add_food.py \
  --name "Starbucks grilled cheese" \
  --serving "1 sandwich" \
  --calories 520 --protein 19 --carbs 47 --fat 28 \
  --fiber 2 --sugar 3 --sodium 1180 --caffeine 0
```

When the user says “it’s Starbucks grilled cheese”, match this library entry and use its exact numbers.

## Logging + totals
Local logs:
- Dir: `/home/desazure/.openclaw/workspace/nutrition/`
- Daily file: `YYYY-MM-DD.jsonl` (append-only)

Log a meal:

```bash
python3 /home/desazure/.openclaw/workspace/skills/macro-tracker/scripts/log_meal.py \
  --date 2026-02-15 \
  --title "Lunch" \
  --items-json '[{"name":"Starbucks grilled cheese","servings":1}]'
```

The script:
- resolves items against the food library when possible
- writes one JSON line per meal into the daily file
- prints updated daily totals

## Google Sheets (optional)
If you want charts, set a Sheet ID under OpenClawShared:

- Put your spreadsheet id into:
  `/home/desazure/.openclaw/workspace/nutrition/sheet_id.txt`

Then `log_meal.py` will also append one row per meal to the sheet (using `gsheets-openclawshared/scripts/append_row.py`).

**Note:** creating the Sheet itself is easiest manually once (in Drive under OpenClawShared). Then paste the sheet id.

## When a photo is ambiguous
Ask only 1–2 clarifying questions (portion / hidden sauces / drink size). Otherwise estimate and label confidence in the meal notes.
