#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/.openclaw/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/session-gc.log"

{
  echo "---- $(date -u '+%Y-%m-%d %H:%M:%S UTC') ----"
  "$SCRIPT_DIR/session_gc.py"
  echo
} >>"$LOG_FILE" 2>&1
