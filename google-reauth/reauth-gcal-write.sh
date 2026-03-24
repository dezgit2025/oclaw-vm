#!/usr/bin/env bash
# reauth-gcal-write.sh — Reauthorize Google Calendar (write) on oclaw VM
# Run directly ON the VM (not from Mac).
# Requires SSH tunnel with port 18797 forwarded from Mac.
# Usage: ~/.openclaw/workspace/ops/google-auth/reauth-gcal-write.sh

set -euo pipefail

VENV_PY="/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"
AUTH_SCRIPT="/home/desazure/.openclaw/workspace/skills/gcal-openclaw/scripts/auth_write.py"
ACCOUNT="assistantdesi@gmail.com"
TOKEN="$HOME/.config/openclaw-gcal/token-write.json"
PORT=18797

echo "==> Killing stale processes on port ${PORT}..."
sudo fuser -k ${PORT}/tcp 2>/dev/null || true
sleep 1

echo "==> Deleting stale token (if exists)..."
rm -f "$TOKEN"

echo ""
echo "==> Running Google Calendar (write) OAuth flow..."
echo "    A Google URL will appear — open it in your Mac browser and approve."
echo ""

"$VENV_PY" "$AUTH_SCRIPT" \
  --account "$ACCOUNT" \
  --token "$TOKEN" \
  --port "$PORT"

echo ""
echo "==> Done. Google Calendar (write) reauth complete."
