#!/usr/bin/env bash
set -euo pipefail

# Wrapper: runs watchdog and writes logs, then cleans old logs (>3 days)
# NOTE: cron often lacks a DBus user session env; set it so `systemctl --user` works.

# Best-effort: infer uid; fall back to 1000 if id lookup fails.
UID_NUM="$(id -u 2>/dev/null || echo 1000)"
export XDG_RUNTIME_DIR="/run/user/${UID_NUM}"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"

WD_DIR="/home/desazure/.openclaw/workspace/manage-oclaw"
LOG_DIR="$HOME/.openclaw/logs/gateway-watchdog"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/$(date -u +%Y-%m-%d).log"

# Run watchdog; always append output
{
  echo "---"
  # Self-check: can we see the user bus? (helps debug cron env issues)
  if [[ -S "${XDG_RUNTIME_DIR}/bus" ]]; then
    echo "[${LOG_FILE##*/}] env_ok=1 XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR}"
  else
    echo "[${LOG_FILE##*/}] env_ok=0 XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR} (no bus socket)"
  fi
  systemctl --user is-active openclaw-gateway.service >/dev/null 2>&1 && echo "[${LOG_FILE##*/}] systemctl_user_ok=1" || echo "[${LOG_FILE##*/}] systemctl_user_ok=0"

  "$WD_DIR/gateway_watchdog.sh"
} >>"$LOG_FILE" 2>&1 || true

# Cleanup: keep only ~2 days of log files (delete older than 2 days)
find "$LOG_DIR" -type f -name '*.log' -mtime +2 -print -delete >>"$LOG_FILE" 2>&1 || true
