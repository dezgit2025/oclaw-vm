#!/usr/bin/env python3
"""Check Tailscale exit node status via watchdog and emit alert text only on state changes.

This is meant to be called frequently (cron). It runs the existing watchdog once,
then compares the state file before/after.

Outputs:
- "OK" when no user-facing alert is needed.
- "ALERT: ..." when the node failed over (down) or recovered.

We treat these as user-facing events:
- exit_node_active flips True -> False  (failover to Azure)
- exit_node_active flips False -> True (restored chromeos-nissa)

State file is written by tailscale_egress_watchdog.py.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

STATE_FILE = Path.home() / ".local/state/openclaw/tailscale-egress-watchdog.state"
WATCHDOG = Path.home() / ".openclaw/workspace/ops/watchdog/tailscale_egress_watchdog.py"
EXIT_NODE = "chromeos-nissa"


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _run_watchdog() -> tuple[int, str]:
    p = subprocess.run([
        "python3",
        str(WATCHDOG),
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, (p.stdout or "").strip()


def main() -> int:
    before = _load_state()
    rc, out = _run_watchdog()
    after = _load_state()

    if rc != 0:
        # Don't spam; just report check failure as an alert because status becomes unknown.
        print(f"ALERT: exit-node check failed to run watchdog (rc={rc}). Output: {out[-300:]}")
        return 0

    b_active = before.get("exit_node_active")
    a_active = after.get("exit_node_active")

    # If we can't determine, stay quiet (or could alert). We'll be conservative and alert.
    if a_active is None:
        print("ALERT: exit-node watchdog ran but state is missing 'exit_node_active' (status unknown).")
        return 0

    if b_active is None:
        # First run / no prior state: no alert.
        print("OK")
        return 0

    if b_active != a_active:
        if a_active is False:
            print(f"ALERT: Tailscale exit node {EXIT_NODE} appears DOWN/unreachable — watchdog failed over to Azure egress.")
        else:
            print(f"ALERT: Tailscale exit node {EXIT_NODE} recovered — watchdog restored residential egress.")
        return 0

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
