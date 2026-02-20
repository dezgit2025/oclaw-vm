#!/usr/bin/env bash
set -euo pipefail

# Runs watchdog log cleanup and appends results into today's watchdog log.
# Intended for cron (every ~3 days).

LOG_DIR="$HOME/.openclaw/logs/gateway-watchdog"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date -u +%Y-%m-%d).log"

{
  echo "---"
  /home/desazure/.openclaw/workspace/ops/watchdog/clean_watchdog_logs.py --keep-days 2
} >>"$LOG_FILE" 2>&1 || true
