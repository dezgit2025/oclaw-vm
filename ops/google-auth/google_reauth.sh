#!/usr/bin/env bash
set -euo pipefail

# Headless-friendly reauth runner for consumer Google OAuth on a headless VM.
# IMPORTANT: Uses loopback redirect (+ SSH tunnel) via per-service --port flags.
# The old code-paste / OOB console flow is brittle and often fails with:
#   Missing required parameter: redirect_uri

ACCOUNT=${1:-}
MODE=${2:-interactive}
# MODE: interactive | print-url-only

if [[ -z "$ACCOUNT" ]]; then
  echo "Usage: $0 <account@gmail.com> [interactive|print-url-only]" >&2
  exit 2
fi

VENV_PY="/home/desazure/.openclaw/workspace/.venv-gmail/bin/python"

run_auth () {
  local name=$1
  shift
  echo ""
  echo "==== $name ===="

  if [[ "$MODE" == "print-url-only" ]]; then
    set +e
    "$VENV_PY" "$@"
    local rc=$?
    set -e
    if [[ $rc -ne 0 ]]; then
      echo "[info] ($name) exited rc=$rc (expected in print-url-only mode)"
    fi
  else
    "$VENV_PY" "$@"
  fi
}

PRINT_FLAG=()
if [[ "$MODE" == "print-url-only" ]]; then
  PRINT_FLAG+=( --print-url-only )
fi

# Gmail drafts
run_auth "gmail" \
  /home/desazure/.openclaw/workspace/skills/gmail-drafts/scripts/auth.py \
  --account "$ACCOUNT" \
  --port 18793 \
  "${PRINT_FLAG[@]}"

# Drive (OpenClawShared)
run_auth "gdrive" \
  /home/desazure/.openclaw/workspace/skills/gdrive-openclawshared/scripts/auth.py \
  --account "$ACCOUNT" \
  --token "$HOME/.config/openclaw-gdrive/token-openclawshared.json" \
  --port 18794 \
  "${PRINT_FLAG[@]}"

# Docs (OpenClawShared)
run_auth "gdocs" \
  /home/desazure/.openclaw/workspace/skills/gdocs-openclawshared/scripts/auth_docs.py \
  --account "$ACCOUNT" \
  --token "$HOME/.config/openclaw-gdrive/token-docs-openclawshared.json" \
  --port 18795 \
  "${PRINT_FLAG[@]}"

# Sheets (OpenClawShared)
run_auth "gsheets" \
  /home/desazure/.openclaw/workspace/skills/gsheets-openclawshared/scripts/auth_sheets.py \
  --account "$ACCOUNT" \
  --token "$HOME/.config/openclaw-gdrive/token-sheets-openclawshared.json" \
  --port 18796 \
  "${PRINT_FLAG[@]}"

# Calendar (readonly)
run_auth "gcal-readonly" \
  /home/desazure/.openclaw/workspace/skills/gcal-openclaw/scripts/auth_readonly.py \
  --account "$ACCOUNT" \
  --token "$HOME/.config/openclaw-gcal/token-readonly.json" \
  --port 18798 \
  "${PRINT_FLAG[@]}"

# Calendar (write)
run_auth "gcal-write" \
  /home/desazure/.openclaw/workspace/skills/gcal-openclaw/scripts/auth_write.py \
  --account "$ACCOUNT" \
  --token "$HOME/.config/openclaw-gcal/token-write.json" \
  --port 18797 \
  "${PRINT_FLAG[@]}"

echo ""
echo "Done. Tip: run audit:" 
echo "  python3 /home/desazure/.openclaw/workspace/ops/google-auth/audit_google_oauth.py"
