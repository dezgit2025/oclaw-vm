#!/usr/bin/env bash
set -euo pipefail

# Installs/updates clawbot ops cron entries for this machine.
# Safe to run multiple times.

OPS_DIR="/home/desazure/.openclaw/workspace/ops"

SESSION_GC="$OPS_DIR/session-gc/run_session_gc.sh"
WATCHDOG="$OPS_DIR/watchdog/run_gateway_watchdog.sh"

if [[ ! -x "$SESSION_GC" ]]; then
  echo "ERROR: missing $SESSION_GC" >&2
  exit 1
fi
if [[ ! -x "$WATCHDOG" ]]; then
  echo "ERROR: missing $WATCHDOG" >&2
  exit 1
fi

TMP=$(mktemp)
crontab -l 2>/dev/null >"$TMP" || true

# Remove prior OpenClaw ops lines (best effort markers)
grep -v -F "$SESSION_GC" "$TMP" | grep -v -F "$WATCHDOG" >"${TMP}.2" || true
mv "${TMP}.2" "$TMP"

# Append fresh entries
cat >>"$TMP" <<EOF

# OpenClaw session log GC (backup >5MB, truncate to ~3MB)
TZ=America/New_York
0 20 * * * $SESSION_GC

# OpenClaw gateway watchdog (no LLM). Every 5 minutes. Logs cleaned after 3 days.
*/5 * * * * $WATCHDOG
EOF

crontab "$TMP"
rm -f "$TMP"

echo "OK: installed cron entries"
crontab -l
