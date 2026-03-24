#!/usr/bin/env bash
# reauth-gmail.sh — Reauthorize Gmail on oclaw VM
# Run directly ON the VM (not from Mac).
# Requires SSH tunnel with port 18793 forwarded from Mac.
# Usage: ~/.openclaw/workspace/ops/google-auth/reauth-gmail.sh

set -euo pipefail

VENV_PY="/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"
AUTH_SCRIPT="/home/desazure/.openclaw/workspace/skills/gmail-drafts/scripts/auth.py"
ACCOUNT="assistantdesi@gmail.com"
TOKEN="$HOME/.config/openclaw-gmail/token-assistantdesi_gmail_com.json"
PORT=18793

echo "==> Killing stale processes on port ${PORT}..."
sudo fuser -k ${PORT}/tcp 2>/dev/null || true
sleep 1

echo "==> Deleting stale token (if exists)..."
rm -f "$TOKEN"

echo ""
echo "==> Running Gmail OAuth flow..."
echo "    A Google URL will appear — open it in your Mac browser and approve."
echo ""

"$VENV_PY" "$AUTH_SCRIPT" \
  --account "$ACCOUNT" \
  --port "$PORT"

echo ""
echo "==> Done. Gmail reauth complete."
