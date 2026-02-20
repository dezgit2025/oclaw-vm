#!/usr/bin/env bash
# Tailscale exit node failover watchdog runner.
# Called by cron every 2 minutes. Logs to daily file.
set -euo pipefail

LOG_DIR="$HOME/.openclaw/logs/tailscale-egress-watchdog"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date -u +%Y-%m-%d).log"

python3 "$HOME/.openclaw/workspace/ops/watchdog/tailscale_egress_watchdog.py" >> "$LOG_FILE" 2>&1
