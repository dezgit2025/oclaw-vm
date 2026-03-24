#!/usr/bin/env bash
# reauth-drive.sh — Reauthorize Google Drive on oclaw VM
# Run directly ON the VM (not from Mac).
# Requires SSH tunnel with port 18794 forwarded from Mac.
# Usage: ~/.openclaw/workspace/ops/google-auth/reauth-drive.sh

set -euo pipefail

VENV_PY="/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"
AUTH_SCRIPT="/home/desazure/.openclaw/workspace/skills/gdrive-openclawshared/scripts/auth.py"
ACCOUNT="assistantdesi@gmail.com"
TOKEN="$HOME/.config/openclaw-gdrive/token-openclawshared.json"
PORT=18794

echo "==> Killing stale processes on port ${PORT}..."
sudo fuser -k ${PORT}/tcp 2>/dev/null || true
sleep 1

echo "==> Deleting stale token (if exists)..."
rm -f "$TOKEN"

echo ""
echo "==> Running GDrive OAuth flow..."
echo "    A Google URL will appear — open it in your Mac browser and approve."
echo ""

"$VENV_PY" "$AUTH_SCRIPT" \
  --account "$ACCOUNT" \
  --token "$TOKEN" \
  --port "$PORT"

echo ""
echo "==> Done. Google Drive reauth complete."
