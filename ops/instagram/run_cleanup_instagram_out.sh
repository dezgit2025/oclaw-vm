#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$HOME/.openclaw/logs/instagram"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/cleanup-$(date -u +%F).log"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "[$TS] starting instagram out cleanup" >> "$LOG"
python3 /home/desazure/.openclaw/workspace/ops/instagram/cleanup_instagram_out.py --keep 30 >> "$LOG" 2>&1
