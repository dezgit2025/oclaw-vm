#!/usr/bin/env python3
"""Daily full-system token ledger.

Goal:
- Compute daily token deltas for the main chat session.
- Sum token usage for per-run isolated sessions (cron/subagent runs), grouped by model.

Data sources:
- ~/.openclaw/agents/main/sessions/sessions.json (session metadata includes model + inputTokens/outputTokens/totalTokens)

Outputs:
- Append JSON line to: /home/desazure/.openclaw/workspace/logs/llm_full_ledger_daily.jsonl
- Update state: /home/desazure/.openclaw/workspace/logs/llm_full_ledger_state.json

Notes:
- The main session token counters are cumulative; we compute deltas vs prior run.
- Cron run sessions appear as keys containing ':cron:' and ':run:' and their token counts are per run.
- We include any session key (excluding main) that contains ':run:' and has updatedAt within the window.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, DefaultDict

SESSIONS_PATH = Path.home() / ".openclaw/agents/main/sessions/sessions.json"
LOG_DIR = Path("/home/desazure/.openclaw/workspace/logs")
OUT_PATH = LOG_DIR / "llm_full_ledger_daily.jsonl"
STATE_PATH = LOG_DIR / "llm_full_ledger_state.json"

MAIN_KEY = "agent:main:main"


def now_ms() -> int:
    return int(time.time() * 1000)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        return load_json(STATE_PATH)
    except Exception:
        return {}


def write_state(state: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def append_line(path: Path, obj: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True) + "\n")


def get_tokens(entry: dict[str, Any]) -> tuple[int, int, int]:
    # sessions.json uses these names
    tin = int(entry.get("inputTokens") or 0)
    tout = int(entry.get("outputTokens") or 0)
    ttot = int(entry.get("totalTokens") or (tin + tout) or 0)
    return tin, tout, ttot


def main() -> None:
    if not SESSIONS_PATH.exists():
        raise SystemExit(f"Missing sessions metadata file: {SESSIONS_PATH}")

    sessions = load_json(SESSIONS_PATH)
    state = read_state()

    ts_ms = now_ms()
    ts_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts_ms / 1000))

    # Window start is last run (ms). If missing, default to 24h.
    start_ms = int(state.get("last_ts_ms") or (ts_ms - 24 * 3600 * 1000))

    # --- Main session delta ---
    main_entry = sessions.get(MAIN_KEY) or {}
    mp = main_entry.get("modelProvider") or "unknown"
    mid = main_entry.get("model") or "unknown"
    main_model = f"{mp}/{mid}"
    main_in, main_out, _ = get_tokens(main_entry)

    prev_main_in = int(state.get("main_inputTokens") or 0)
    prev_main_out = int(state.get("main_outputTokens") or 0)

    delta_main_in = max(main_in - prev_main_in, 0)
    delta_main_out = max(main_out - prev_main_out, 0)
    delta_main_total = delta_main_in + delta_main_out

    # --- Per-run sessions (cron/subagents) within window ---
    by_model: DefaultDict[str, dict[str, int]] = defaultdict(lambda: {"tokens_in": 0, "tokens_out": 0, "tokens_total": 0})

    def add(model: str, tin: int, tout: int, ttot: int):
        m = by_model[model]
        m["tokens_in"] += tin
        m["tokens_out"] += tout
        m["tokens_total"] += ttot

    # include main delta under its model
    add(str(main_model), delta_main_in, delta_main_out, delta_main_total)

    run_sessions_count = 0
    for k, v in sessions.items():
        if k == MAIN_KEY:
            continue
        if ":run:" not in k:
            continue
        upd = int(v.get("updatedAt") or 0)
        if upd < start_ms or upd > ts_ms:
            continue
        mp = v.get("modelProvider") or "unknown"
        mid = v.get("model") or "unknown"
        model = f"{mp}/{mid}"
        tin, tout, ttot = get_tokens(v)
        # For run sessions, totals should already be per-run. If not, this will overcount,
        # but these sessions are typically ephemeral.
        add(model, tin, tout, ttot)
        run_sessions_count += 1

    out = {
        "ts_utc": ts_utc,
        "window_start_ms": start_ms,
        "window_end_ms": ts_ms,
        "main_session": {
            "sessionKey": MAIN_KEY,
            "model": main_model,
            "delta_tokens_in": delta_main_in,
            "delta_tokens_out": delta_main_out,
            "delta_tokens_total": delta_main_total,
            "absolute_inputTokens": main_in,
            "absolute_outputTokens": main_out,
        },
        "run_sessions_in_window": run_sessions_count,
        "totals_by_model": dict(sorted(by_model.items(), key=lambda kv: kv[0])),
    }

    append_line(OUT_PATH, out)

    # update state
    state["last_ts_ms"] = ts_ms
    state["main_inputTokens"] = main_in
    state["main_outputTokens"] = main_out
    write_state(state)

    print("OK")
    print(json.dumps({"ts_utc": ts_utc, "models": out["totals_by_model"], "run_sessions": run_sessions_count}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
