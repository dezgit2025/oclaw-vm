#!/usr/bin/env python3
"""Tailscale exit node failover watchdog.

Checks if the exit node is reachable. If 2 consecutive failures, clears the
exit node so VM falls back to Azure native egress. Re-enables when reachable.

State file: ~/.local/state/openclaw/tailscale-egress-watchdog.state
Logs:       ~/.openclaw/logs/tailscale-egress-watchdog/YYYY-MM-DD.log
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

EXIT_NODE = "chromeos-nissa"
EXIT_NODE_IP = "100.124.62.63"
FAIL_THRESHOLD = 2
PING_TIMEOUT_S = 5

STATE_FILE = Path.home() / ".local/state/openclaw/tailscale-egress-watchdog.state"
LOG_DIR = Path.home() / ".openclaw/logs/tailscale-egress-watchdog"


def ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log(msg: str) -> None:
    line = f"[{ts()}] {msg}"
    print(line, flush=True)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"consecutive_failures": 0, "exit_node_active": True, "last_transition": ""}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=timeout)
        return p.returncode, (p.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return 1, "timeout"


def ping_exit_node() -> bool:
    rc, out = run(["tailscale", "ping", "--timeout", f"{PING_TIMEOUT_S}s",
                    "--c", "1", EXIT_NODE], timeout=PING_TIMEOUT_S + 5)
    return rc == 0 and "pong" in out.lower()


def is_exit_node_active() -> bool:
    """Check if any exit node is currently set (by looking for ExitNode=true in peers)."""
    rc, out = run(["tailscale", "status", "--json"], timeout=10)
    if rc != 0:
        return False
    try:
        data = json.loads(out)
        for _, peer in data.get("Peer", {}).items():
            if peer.get("ExitNode", False):
                return True
    except (json.JSONDecodeError, KeyError):
        pass
    return False


def set_exit_node(node: str) -> bool:
    if node:
        rc, out = run(["sudo", "tailscale", "set", f"--exit-node={node}"])
    else:
        rc, out = run(["sudo", "tailscale", "set", "--exit-node="])
    log(f"tailscale set exit-node={node or '(none)'} rc={rc} out={out}")
    return rc == 0


def main() -> int:
    state = load_state()
    reachable = ping_exit_node()

    if reachable:
        if state["consecutive_failures"] > 0:
            log(f"exit node {EXIT_NODE} reachable again (was {state['consecutive_failures']} failures)")
        state["consecutive_failures"] = 0

        if not state.get("exit_node_active", True):
            log(f"re-enabling exit node {EXIT_NODE}")
            if set_exit_node(EXIT_NODE):
                state["exit_node_active"] = True
                state["last_transition"] = f"{ts()} restored {EXIT_NODE}"
            else:
                log("ERROR: failed to re-enable exit node")
        else:
            if not is_exit_node_active():
                log(f"exit node not set, re-enabling {EXIT_NODE}")
                set_exit_node(EXIT_NODE)

    else:
        state["consecutive_failures"] += 1
        log(f"exit node {EXIT_NODE} unreachable (consecutive={state['consecutive_failures']})")

        if state["consecutive_failures"] >= FAIL_THRESHOLD and state.get("exit_node_active", True):
            log(f"FAILOVER: clearing exit node after {FAIL_THRESHOLD} failures -> Azure egress")
            if set_exit_node(""):
                state["exit_node_active"] = False
                state["last_transition"] = f"{ts()} failover to Azure"
            else:
                log("ERROR: failed to clear exit node")

    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
