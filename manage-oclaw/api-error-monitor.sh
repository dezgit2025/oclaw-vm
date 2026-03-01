#!/bin/bash
# API Error 500 Monitor for Claude Code
# Scans Claude Code debug logs for 500 errors and reports frequency
# Usage: ./api-error-monitor.sh [hours_back]
#   hours_back: how many hours to look back (default: 24)

HOURS_BACK="${1:-24}"
LOG_DIR="$HOME/.claude/debug"
REPORT_FILE="$HOME/.claude/debug/api-500-report.log"

echo "=== Claude Code API 500 Error Report ==="
echo "Scanning last ${HOURS_BACK}h of logs"
echo "Time: $(date)"
echo "---"

if [ ! -d "$LOG_DIR" ]; then
    echo "No debug log directory found at $LOG_DIR"
    echo "Enable debug logging: CLAUDE_CODE_DEBUG=1"
    exit 0
fi

# Count 500 errors in recent logs
CUTOFF=$(date -v-${HOURS_BACK}H +%Y-%m-%d 2>/dev/null || date -d "${HOURS_BACK} hours ago" +%Y-%m-%d 2>/dev/null)

echo ""
echo "Checking for API 500 errors since $CUTOFF..."
echo ""

# Search for 500 errors in log files
TOTAL_500=0
TOTAL_REQUESTS=0

for logfile in "$LOG_DIR"/*.log; do
    [ -f "$logfile" ] || continue

    # Skip files older than cutoff
    FILE_DATE=$(stat -f "%Sm" -t "%Y-%m-%d" "$logfile" 2>/dev/null || stat -c "%y" "$logfile" 2>/dev/null | cut -d' ' -f1)
    if [[ "$FILE_DATE" < "$CUTOFF" ]]; then
        continue
    fi

    count_500=$(grep -c "500\|Internal server error\|api_error" "$logfile" 2>/dev/null || echo 0)
    if [ "$count_500" -gt 0 ]; then
        TOTAL_500=$((TOTAL_500 + count_500))
        echo "  $logfile: $count_500 error(s)"
    fi
done

echo ""
echo "Total 500 errors found: $TOTAL_500"

# Also check if any errors correlate with hook timing
echo ""
echo "=== Hook Timing Check ==="
echo "Looking for hook-correlated errors..."

for logfile in "$LOG_DIR"/*.log; do
    [ -f "$logfile" ] || continue
    FILE_DATE=$(stat -f "%Sm" -t "%Y-%m-%d" "$logfile" 2>/dev/null || stat -c "%y" "$logfile" 2>/dev/null | cut -d' ' -f1)
    if [[ "$FILE_DATE" < "$CUTOFF" ]]; then
        continue
    fi

    hook_errors=$(grep -B2 "500\|Internal server error" "$logfile" 2>/dev/null | grep -c "hook\|before_agent\|clawbot-memory" || echo 0)
    if [ "$hook_errors" -gt 0 ]; then
        echo "  WARNING: $logfile has $hook_errors errors near hook execution"
    fi
done

echo ""
echo "=== Anthropic Status ==="
echo "Check: https://status.anthropic.com"
echo "Issues: https://github.com/anthropics/claude-code/issues"
echo ""

# Append summary to report file
echo "$(date +%Y-%m-%dT%H:%M:%S) | 500_count=$TOTAL_500 | window=${HOURS_BACK}h" >> "$REPORT_FILE"
echo "Report appended to $REPORT_FILE"
