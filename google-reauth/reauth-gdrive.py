#!/usr/bin/env python3
"""Reauth Google Drive on oclaw VM.

Kills stale processes on port 18794, waits 1s, then runs the OAuth flow.
Requires SSH tunnel with port 18794 forwarded to the VM.
"""

import subprocess
import sys
import time

VM_HOST = "oclaw"
VENV_PY = "/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"
AUTH_SCRIPT = "/home/desazure/.openclaw/workspace/skills/gdrive-openclawshared/scripts/auth.py"
ACCOUNT = "assistantdesi@gmail.com"
TOKEN = "~/.config/openclaw-gdrive/token-openclawshared.json"
PORT = 18794


def run(cmd, check=True):
    print(f">>> {cmd}")
    return subprocess.run(cmd, shell=True, check=check)


def main():
    print("Step 1: Kill stale processes on OAuth ports")
    run(
        f'ssh {VM_HOST} "sudo fuser -k 18793/tcp 18794/tcp 18795/tcp '
        f'18796/tcp 18797/tcp 18798/tcp 2>/dev/null; echo done"',
        check=False,
    )

    print("\nWaiting 1 second...")
    time.sleep(1)

    print("\nStep 2: Run GDrive OAuth (open the URL in your browser)")
    result = run(
        f'ssh {VM_HOST} "{VENV_PY} {AUTH_SCRIPT} '
        f"--account {ACCOUNT} --token {TOKEN} --port {PORT}\"",
        check=False,
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
