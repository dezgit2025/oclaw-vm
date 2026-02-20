#!/usr/bin/env python3
"""Monthly token+cost report for Foundry models.

Reads:
- /home/desazure/.openclaw/workspace/logs/llm_full_ledger_daily.jsonl
- pricing file: ops/llm-ledger/pricing_usd_per_1m_tokens.json

Outputs a month summary with:
- input_tokens, input_cost
- output_tokens, output_cost
- total_cost

Default: month-to-date for current UTC month.

Usage:
  python3 monthly_cost_report.py                 # current month-to-date
  python3 monthly_cost_report.py --month 2026-02 # specific month
  python3 monthly_cost_report.py --all           # all months present

"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEDGER_PATH = Path("/home/desazure/.openclaw/workspace/logs/llm_full_ledger_daily.jsonl")
PRICING_PATH = Path("/home/desazure/.openclaw/workspace/ops/llm-ledger/pricing_usd_per_1m_tokens.json")


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def ym(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def money(x: float) -> str:
    return f"${x:,.4f}" if x < 100 else f"${x:,.2f}"


def load_pricing() -> dict[str, Any]:
    if not PRICING_PATH.exists():
        raise SystemExit(f"Missing pricing file: {PRICING_PATH}")
    return json.loads(PRICING_PATH.read_text(encoding="utf-8"))


def get_rates(pricing: dict[str, Any], model: str) -> tuple[float | None, float | None]:
    m = (pricing.get("models") or {}).get(model) or {}
    return m.get("input"), m.get("output")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="YYYY-MM (report this month only)")
    ap.add_argument("--all", action="store_true", help="Report all months found")
    args = ap.parse_args()

    if not LEDGER_PATH.exists():
        raise SystemExit(f"Missing ledger file: {LEDGER_PATH}")

    pricing = load_pricing()

    rows = [json.loads(l) for l in LEDGER_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]

    # Aggregate: month -> model -> in/out
    agg: dict[str, dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(lambda: {"in": 0, "out": 0}))

    for r in rows:
        ts = parse_ts(r["ts_utc"])
        month = ym(ts)
        totals = r.get("totals_by_model") or {}
        for model, t in totals.items():
            if not str(model).startswith("foundry/"):
                continue
            agg[month][model]["in"] += int(t.get("tokens_in") or 0)
            agg[month][model]["out"] += int(t.get("tokens_out") or 0)

    months = sorted(agg.keys())
    if args.month:
        months = [args.month]
    elif not args.all:
        # current UTC month
        months = [ym(datetime.now(timezone.utc))]

    out_blocks = []
    for m in months:
        models = agg.get(m, {})
        total_in = sum(v["in"] for v in models.values())
        total_out = sum(v["out"] for v in models.values())

        total_in_cost = 0.0
        total_out_cost = 0.0

        model_lines = []
        for model in sorted(models.keys()):
            tin = models[model]["in"]
            tout = models[model]["out"]
            rin, rout = get_rates(pricing, model)
            in_cost = (tin / 1_000_000.0) * float(rin) if rin is not None else None
            out_cost = (tout / 1_000_000.0) * float(rout) if rout is not None else None

            if in_cost is not None:
                total_in_cost += in_cost
            if out_cost is not None:
                total_out_cost += out_cost

            model_lines.append(
                {
                    "model": model,
                    "input_tokens": tin,
                    "input_cost": in_cost,
                    "output_tokens": tout,
                    "output_cost": out_cost,
                }
            )

        block = {
            "month": m,
            "foundry_input_tokens": total_in,
            "foundry_output_tokens": total_out,
            "foundry_input_cost": total_in_cost,
            "foundry_output_cost": total_out_cost,
            "foundry_total_cost": total_in_cost + total_out_cost,
            "by_model": model_lines,
        }
        out_blocks.append(block)

    # Print human summary
    for b in out_blocks:
        print(f"AI Foundry monthly report — {b['month']}")
        print(f"- Input tokens:  {b['foundry_input_tokens']:,}  | cost: {money(b['foundry_input_cost'])}")
        print(f"- Output tokens: {b['foundry_output_tokens']:,}  | cost: {money(b['foundry_output_cost'])}")
        print(f"- Total cost:    {money(b['foundry_total_cost'])}")
        if b["by_model"]:
            print("  By model:")
            for ml in b["by_model"]:
                ic = "(rate missing)" if ml["input_cost"] is None else money(ml["input_cost"])
                oc = "(rate missing)" if ml["output_cost"] is None else money(ml["output_cost"])
                print(f"  - {ml['model']}: in {ml['input_tokens']:,} ({ic}), out {ml['output_tokens']:,} ({oc})")
        else:
            print("  (No Foundry usage logged for this month yet.)")
        print()

    # Also emit machine-readable JSON (last line)
    print(json.dumps({"reports": out_blocks}, sort_keys=True))


if __name__ == "__main__":
    main()
