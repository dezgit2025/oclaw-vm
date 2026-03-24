#!/usr/bin/env bash
# reauth-docs.sh — Reauthorize Google Docs on oclaw VM
# Run directly ON the VM (not from Mac).
# Requires SSH tunnel with port 18795 forwarded from Mac.
# Usage: ~/.openclaw/workspace/ops/google-auth/reauth-docs.sh

set -euo pipefail

VENV_PY="/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"
AUTH_SCRIPT="/home/desazure/.openclaw/workspace/skills/gdocs-openclawshared/scripts/auth_docs.py"
ACCOUNT="assistantdesi@gmail.com"
TOKEN="$HOME/.config/openclaw-gdrive/token-docs-openclawshared.json"
PORT=18795

echo "==> Killing stale processes on port ${PORT}..."
sudo fuser -k ${PORT}/tcp 2>/dev/null || true
sleep 1

echo "==> Deleting stale token (if exists)..."
rm -f "$TOKEN"

echo ""
echo "==> Running Google Docs OAuth flow..."
echo "    A Google URL will appear — open it in your Mac browser and approve."
echo ""

"$VENV_PY" "$AUTH_SCRIPT" \
  --account "$ACCOUNT" \
  --token "$TOKEN" \
  --port "$PORT"

echo ""
echo "==> Done. Google Docs reauth complete."
