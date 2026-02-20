#!/usr/bin/env bash
# foundry-monitor.sh — Deterministic health check for the Foundry MI proxy.
# Runs 3 checks: systemd service, /healthz, and a chat completion roundtrip.
# On failure: prints ALERT:<details> to stdout (caller handles Telegram/email).
# On success: prints OK to stdout.
#
# Usage:  bash foundry-monitor.sh
# Exit 0 = all checks passed, Exit 1 = at least one check failed.

set -euo pipefail

PROXY_URL="http://127.0.0.1:18791"
SERVICE_NAME="openclaw-foundry-proxy.service"
MODEL="foundry/gpt-4.1-mini"
SENTINEL="OK_foundry_mini_monitor"
TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

fail() {
  echo "ALERT: $1"
  exit 1
}

# ---------- CHECK 1: systemd service ----------
svc_state=$(systemctl --user is-active "$SERVICE_NAME" 2>&1 || true)
if [[ "$svc_state" != "active" ]]; then
  fail "[$TS] Foundry proxy monitor failed | check: systemd | state: $svc_state (expected: active)"
fi

# ---------- CHECK 2: /healthz ----------
healthz_file=$(mktemp /tmp/foundry_healthz_XXXXXX.json)
healthz_code=$(curl -sS -o "$healthz_file" -w '%{http_code}' "${PROXY_URL}/healthz" 2>&1) || true

if [[ "$healthz_code" != "200" ]]; then
  body=$(head -c 500 "$healthz_file" 2>/dev/null || echo "(empty)")
  rm -f "$healthz_file"
  fail "[$TS] Foundry proxy monitor failed | check: healthz_http | http_code: $healthz_code | body: $body"
fi

# Parse JSON with python3 — check that ok == true
healthz_ok=$(python3 -c "
import json, sys
try:
    d = json.load(open('$healthz_file'))
    print('yes' if d.get('ok') is True else 'no')
except Exception as e:
    print(f'error:{e}')
" 2>&1)
rm -f "$healthz_file"

if [[ "$healthz_ok" != "yes" ]]; then
  fail "[$TS] Foundry proxy monitor failed | check: healthz_json | result: $healthz_ok"
fi

# ---------- CHECK 3: chat completions ----------
chat_file=$(mktemp /tmp/foundry_chat_XXXXXX.json)
chat_req=$(mktemp /tmp/foundry_chat_req_XXXXXX.json)

cat > "$chat_req" <<JSON
{
  "model": "$MODEL",
  "messages": [
    {"role": "user", "content": "Reply with exactly: $SENTINEL"}
  ],
  "max_tokens": 32,
  "temperature": 0
}
JSON

chat_code=$(curl -sS -o "$chat_file" -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -d @"$chat_req" \
  "${PROXY_URL}/v1/chat/completions" 2>&1) || true
rm -f "$chat_req"

if ! [[ "$chat_code" =~ ^[0-9]{3}$ ]]; then
  rm -f "$chat_file"
  fail "[$TS] Foundry proxy monitor failed | check: chat_curl | error: $chat_code"
fi

if [[ "$chat_code" != "200" ]]; then
  body=$(head -c 800 "$chat_file" 2>/dev/null || echo "(empty)")
  rm -f "$chat_file"
  fail "[$TS] Foundry proxy monitor failed | check: chat_http | http_code: $chat_code | body: $body"
fi

# Parse response JSON with python3
chat_result=$(python3 -c "
import json, sys
try:
    d = json.load(open('$chat_file'))
    msg = ((d.get('choices') or [{}])[0].get('message') or {})
    content = msg.get('content') or msg.get('reasoning_content') or ''
    if '$SENTINEL' in content:
        print('yes')
    else:
        print(f'no:content={content!r:.200}')
except Exception as e:
    print(f'error:{e}')
" 2>&1)
rm -f "$chat_file"

if [[ "$chat_result" != "yes" ]]; then
  fail "[$TS] Foundry proxy monitor failed | check: chat_response | result: $chat_result"
fi

# ---------- ALL CHECKS PASSED ----------
echo "OK"
exit 0
