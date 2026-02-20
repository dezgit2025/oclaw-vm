#!/usr/bin/env python3
"""Restart the OpenClaw gateway (systemd --user unit) with structured stdout for logging.

Designed to be called from gateway_watchdog.sh so all output is appended to the same
~/.openclaw/logs/gateway-watchdog/YYYY-MM-DD.log file.

Relies on environment for systemd --user DBus access:
- XDG_RUNTIME_DIR=/run/user/<uid>
- DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<uid>/bus
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

UNIT_DEFAULT = "openclaw-gateway.service"


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, (p.stdout or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", default=UNIT_DEFAULT)
    ap.add_argument("--wait", type=float, default=2.0, help="seconds to wait after restart")
    ap.add_argument("--reason", default="watchdog", help="freeform reason tag")
    args = ap.parse_args()

    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    xdg = os.environ.get("XDG_RUNTIME_DIR", "")
    dbus = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "")

    print(f"[{ts}] restart_gateway.py start unit={args.unit} reason={args.reason}")
    print(f"[{ts}] env XDG_RUNTIME_DIR={xdg} DBUS_SESSION_BUS_ADDRESS={dbus}")

    rc0, out0 = run(["systemctl", "--user", "is-active", args.unit])
    ts0 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts0}] pre is-active rc={rc0} out={out0}")

    rc, out = run(["systemctl", "--user", "restart", args.unit])
    ts1 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts1}] restart rc={rc} out={out}")
    if rc != 0:
        return rc

    time.sleep(max(args.wait, 0.0))

    rc2, out2 = run(["systemctl", "--user", "is-active", args.unit])
    ts2 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts2}] post is-active rc={rc2} out={out2}")

    return 0 if rc2 == 0 else 4


if __name__ == "__main__":
    sys.exit(main())
