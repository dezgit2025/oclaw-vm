#!/usr/bin/env python3
"""Session format watchdog for the clawbot memory extraction pipeline.

Monitors openclaw session log format for breaking changes (e.g. version bumps,
new event types) that could silently break the smart_extractor.py sweep.
Run via cron before the daily extraction window so format regressions are
caught before data is lost.

Exit codes:
    0 - All checks passed
    1 - WARNING (unknown event types found, extraction likely still works)
    2 - CRITICAL (version mismatch or canary extraction failed)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

KNOWN_EVENT_TYPES = {
    "session",
    "message",
    "model_change",
    "thinking_level_change",
    "custom",
    "compaction",
}

DEFAULT_EXPECTED_VERSION = 3
DEFAULT_SESSION_DIR = "~/.openclaw/agents/main/sessions/"
DEFAULT_STATE_FILE = "~/.local/state/openclaw/session-format-watchdog.state"
DEFAULT_LOG_DIR = "~/.openclaw/logs/session-format-watchdog/"


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def setup_logging(log_dir):
    """Ensure log directory exists and return today's log path."""
    log_dir = Path(log_dir).expanduser()
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return log_dir / f"{today}.log"


def log(log_file, level, message):
    """Append a log line and mirror to stdout for cron mail."""
    ts = now_iso()
    line = f"[{ts}] {level} {message}"
    print(line)
    with open(log_file, "a") as f:
        f.write(line + "\n")


def load_state(state_file):
    """Load state from JSON file or return defaults."""
    state_file = Path(state_file).expanduser()
    if state_file.exists():
        try:
            with open(state_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "expected_version": DEFAULT_EXPECTED_VERSION,
        "last_checked": None,
        "last_version_seen": None,
        "known_event_types": sorted(KNOWN_EVENT_TYPES),
        "unknown_types_seen": [],
        "canary_result": "skipped",
        "canary_detail": None,
        "consecutive_failures": 0,
        "last_session_file": None,
        "last_session_id": None,
    }


def save_state(state_file, state):
    """Write state as pretty-printed JSON."""
    state_file = Path(state_file).expanduser()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def find_newest_session(session_dir):
    """Return the most recently modified .jsonl file, or None."""
    session_dir = Path(session_dir).expanduser()
    if not session_dir.is_dir():
        return None
    sessions = list(session_dir.glob("*.jsonl"))
    if not sessions:
        return None
    return max(sessions, key=lambda p: p.stat().st_mtime)


def parse_header(session_path):
    """Read the first line of a session file and extract version + type + id."""
    with open(session_path) as f:
        first_line = f.readline().strip()
    if not first_line:
        return None, None, None
    try:
        header = json.loads(first_line)
        return header.get("version"), header.get("type"), header.get("id")
    except json.JSONDecodeError:
        return None, None, None


def scan_event_types(session_path, max_lines=50):
    """Scan up to max_lines and return the set of event type values found."""
    types_found = set()
    with open(session_path) as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                t = event.get("type")
                if t:
                    types_found.add(t)
            except json.JSONDecodeError:
                continue
    return types_found


def run_canary(session_path, script_dir, log_file):
    """Run smart_extractor.py canary if available. Returns (result, detail)."""
    extractor = script_dir / "smart_extractor.py"
    if not extractor.exists():
        return "skipped", "smart_extractor.py not found"

    # Check if canary subcommand is supported by looking at help output
    venv_python = script_dir / ".venv" / "bin" / "python3"
    python_cmd = str(venv_python) if venv_python.exists() else "python3"

    cmd = [python_cmd, str(extractor), "canary", str(session_path)]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return "ok", result.stdout.strip()[:200] or "canary passed"
        elif result.returncode == 2 and "usage:" in result.stderr.lower():
            # argparse exits with code 2 for unrecognized subcommands
            return "skipped", "canary subcommand not supported"
        else:
            detail = (result.stderr.strip() or result.stdout.strip())[:200]
            return "fail", detail or f"exit code {result.returncode}"
    except subprocess.TimeoutExpired:
        return "fail", "canary timed out after 30s"
    except FileNotFoundError:
        return "skipped", "python interpreter not found"
    except OSError as e:
        return "skipped", str(e)[:200]


def main():
    parser = argparse.ArgumentParser(
        description="Monitor openclaw session format for breaking changes."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run even if already checked today. Resets consecutive_failures.",
    )
    parser.add_argument(
        "--state-file",
        default=os.environ.get("STATE_FILE", DEFAULT_STATE_FILE),
        help="Path to state file (default: %(default)s)",
    )
    parser.add_argument(
        "--session-dir",
        default=os.environ.get("SESSION_DIR", DEFAULT_SESSION_DIR),
        help="Path to session directory (default: %(default)s)",
    )
    parser.add_argument(
        "--log-dir",
        default=os.environ.get("LOG_DIR", DEFAULT_LOG_DIR),
        help="Path to log directory (default: %(default)s)",
    )
    args = parser.parse_args()

    log_file = setup_logging(args.log_dir)
    state = load_state(args.state_file)
    exit_code = 0

    if args.force:
        state["consecutive_failures"] = 0

    # 1. Find newest session
    newest = find_newest_session(args.session_dir)
    if newest is None:
        log(log_file, "INFO", "No sessions found")
        state["last_checked"] = now_iso()
        save_state(args.state_file, state)
        return 0

    log(log_file, "INFO", f"Checking session: {newest.name}")

    # 2. Parse header
    version, header_type, session_id = parse_header(newest)
    state["last_session_file"] = newest.name
    state["last_session_id"] = session_id

    if version is None:
        log(log_file, "CRITICAL", f"Failed to parse header from {newest.name}")
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        state["last_checked"] = now_iso()
        save_state(args.state_file, state)
        return 2

    if header_type != "session":
        log(log_file, "WARNING", f"Header type is '{header_type}', expected 'session'")

    state["last_version_seen"] = version

    # 3. Version check
    expected = state.get("expected_version", DEFAULT_EXPECTED_VERSION)
    if version != expected:
        log(
            log_file,
            "CRITICAL",
            f"Version mismatch: expected {expected}, got {version}. "
            f"Session format may have changed — extraction pipeline at risk.",
        )
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        exit_code = max(exit_code, 2)
    else:
        log(log_file, "INFO", f"Version OK: {version}")

    # 4. Scan event types
    types_found = scan_event_types(newest)
    unknown = types_found - KNOWN_EVENT_TYPES
    if unknown:
        unknown_list = sorted(unknown)
        log(
            log_file,
            "WARNING",
            f"Unknown event types found: {unknown_list}. "
            f"Extraction may miss or misparse these events.",
        )
        prev_unknown = set(state.get("unknown_types_seen", []))
        state["unknown_types_seen"] = sorted(prev_unknown | unknown)
        exit_code = max(exit_code, 1)
    else:
        log(log_file, "INFO", f"Event types OK: {sorted(types_found)}")
        state["unknown_types_seen"] = []

    # 5. Canary extraction
    script_dir = Path(__file__).resolve().parent
    canary_result, canary_detail = run_canary(newest, script_dir, log_file)
    state["canary_result"] = canary_result
    state["canary_detail"] = canary_detail

    if canary_result == "ok":
        log(log_file, "INFO", f"Canary extraction passed: {canary_detail}")
    elif canary_result == "skipped":
        log(
            log_file,
            "INFO",
            f"Canary extraction skipped ({canary_detail})",
        )
    else:
        log(log_file, "CRITICAL", f"Canary extraction failed: {canary_detail}")
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        exit_code = max(exit_code, 2)

    # Reset consecutive_failures on clean run
    if exit_code == 0:
        state["consecutive_failures"] = 0

    # 6. Save state
    state["last_checked"] = now_iso()
    state["known_event_types"] = sorted(KNOWN_EVENT_TYPES)
    save_state(args.state_file, state)

    level = {0: "INFO", 1: "WARNING", 2: "CRITICAL"}.get(exit_code, "INFO")
    log(
        log_file,
        level,
        f"Watchdog complete — exit {exit_code}, "
        f"consecutive_failures={state['consecutive_failures']}",
    )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
