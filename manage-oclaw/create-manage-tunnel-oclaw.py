#!/usr/bin/env python3
"""Manage SSH tunnel to oclaw VM (ports 18792-18795)."""

import subprocess
import signal
import sys
import time
import os


TUNNEL_CMD = ["ssh", "-N", "-L", "18792:127.0.0.1:18792", "-L", "18793:127.0.0.1:18793", "-L", "18794:127.0.0.1:18794", "-L", "18795:127.0.0.1:18795", "oclaw"]
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tunnel-oclaw.pid")


def is_tunnel_running():
    """Check if the tunnel process is still running."""
    if not os.path.exists(PID_FILE):
        return False, None
    with open(PID_FILE) as f:
        pid = int(f.read().strip())
    try:
        os.kill(pid, 0)
        return True, pid
    except ProcessLookupError:
        os.remove(PID_FILE)
        return False, None


def start_tunnel(foreground=False):
    """Start the SSH tunnel."""
    running, pid = is_tunnel_running()
    if running:
        print(f"Tunnel already running (PID {pid})")
        return

    print(f"Starting tunnel: {' '.join(TUNNEL_CMD)}")

    if foreground:
        proc = subprocess.Popen(TUNNEL_CMD)
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        print(f"Tunnel started (PID {proc.pid}) - press Ctrl+C to stop")

        def cleanup(signum, frame):
            print("\nStopping tunnel...")
            proc.terminate()
            proc.wait()
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            sys.exit(0)

        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)
        proc.wait()
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        print("Tunnel stopped.")
    else:
        proc = subprocess.Popen(
            TUNNEL_CMD,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        time.sleep(1)
        if proc.poll() is None:
            print(f"Tunnel started in background (PID {proc.pid})")
        else:
            print(f"Tunnel failed to start (exit code {proc.returncode})")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)


def stop_tunnel():
    """Stop the SSH tunnel."""
    running, pid = is_tunnel_running()
    if not running:
        print("No tunnel running.")
        return
    print(f"Stopping tunnel (PID {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except ProcessLookupError:
        pass
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    print("Tunnel stopped.")


def status():
    """Show tunnel status."""
    running, pid = is_tunnel_running()
    if running:
        print(f"Tunnel is RUNNING (PID {pid})")
        print(f"  Local:  127.0.0.1:18792-18795")
        print(f"  Remote: oclaw -> 127.0.0.1:18792-18795")
    else:
        print("Tunnel is NOT running.")


def usage():
    print(f"Usage: {sys.argv[0]} <command>")
    print()
    print("Commands:")
    print("  start       Start tunnel in background")
    print("  start -f    Start tunnel in foreground (Ctrl+C to stop)")
    print("  stop        Stop tunnel")
    print("  restart     Restart tunnel")
    print("  status      Show tunnel status")


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "start":
        fg = "-f" in sys.argv or "--foreground" in sys.argv
        start_tunnel(foreground=fg)
    elif cmd == "stop":
        stop_tunnel()
    elif cmd == "restart":
        stop_tunnel()
        start_tunnel()
    elif cmd == "status":
        status()
    else:
        usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
