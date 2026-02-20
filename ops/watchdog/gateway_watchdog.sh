#!/usr/bin/env bash
set -euo pipefail

# Lightweight OpenClaw gateway watchdog (no LLM calls)
# - checks systemd unit active
# - checks TCP port open (18789)
# - on 2 consecutive failures, restarts the gateway
# - rate-limits restarts

UNIT="openclaw-gateway.service"
HOST="127.0.0.1"
PORT="18789"

STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/openclaw"
STATE_FILE="$STATE_DIR/gateway-watchdog.state"
mkdir -p "$STATE_DIR"

# Tuning
FAIL_THRESHOLD=2
RESTART_MIN_INTERVAL_SEC=$((30*60))

now_epoch() { date +%s; }

read_state() {
  # format: fail_count last_restart_epoch
  if [[ -f "$STATE_FILE" ]]; then
    read -r fail_count last_restart_epoch < "$STATE_FILE" || true
  fi
  fail_count="${fail_count:-0}"
  last_restart_epoch="${last_restart_epoch:-0}"
}

write_state() {
  printf "%s %s\n" "$fail_count" "$last_restart_epoch" > "$STATE_FILE"
}

is_unit_active() {
  # Return codes:
  # - 0: active
  # - 1: inactive/failed/etc
  # - 3: unknown (couldn't query systemd user bus)
  if systemctl --user is-active --quiet "$UNIT"; then
    return 0
  fi

  # If systemctl can't connect to the user bus (common under cron), treat as unknown.
  if systemctl --user show "$UNIT" -p ActiveState >/dev/null 2>&1; then
    return 1
  else
    return 3
  fi
}

is_port_open() {
  # bash TCP connect with a short timeout using timeout(1)
  timeout 1 bash -c "</dev/tcp/$HOST/$PORT" >/dev/null 2>&1
}

main() {
  read_state

  ts_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  ok_unit=0
  unit_unknown=0
  ok_port=0

  if is_unit_active; then
    ok_unit=1
  else
    rc=$?
    if [[ $rc -eq 3 ]]; then
      unit_unknown=1
    fi
  fi

  if is_port_open; then ok_port=1; fi

  if [[ "$ok_unit" -eq 1 && "$ok_port" -eq 1 ]]; then
    # healthy
    if [[ "$fail_count" -ne 0 ]]; then
      echo "[$ts_utc] OK (recovered). unit=active port=open (was failing count=$fail_count)"
    fi
    fail_count=0
    write_state
    exit 0
  fi

  # If we can't query systemd user bus, do not take destructive action.
  # (This can happen in cron if DBUS/XDG env isn't set.)
  if [[ "$unit_unknown" -eq 1 ]]; then
    echo "[$ts_utc] WARN unit_status=unknown (cannot reach systemd --user bus). port_open=$ok_port. Skipping restart logic."
    fail_count=0
    write_state
    exit 0
  fi

  # unhealthy
  fail_count=$((fail_count + 1))
  echo "[$ts_utc] FAIL count=$fail_count unit_active=$ok_unit port_open=$ok_port"

  if [[ "$fail_count" -lt "$FAIL_THRESHOLD" ]]; then
    write_state
    exit 1
  fi

  # threshold reached: attempt restart if not rate-limited
  epoch_now="$(now_epoch)"
  since_restart=$((epoch_now - last_restart_epoch))
  if [[ "$last_restart_epoch" -ne 0 && "$since_restart" -lt "$RESTART_MIN_INTERVAL_SEC" ]]; then
    echo "[$ts_utc] SKIP restart (rate-limited). since_last_restart=${since_restart}s"
    write_state
    exit 2
  fi

  echo "[$ts_utc] RESTARTING $UNIT"
  systemctl --user restart "$UNIT"
  last_restart_epoch="$epoch_now"
  fail_count=0
  write_state

  # After restart, wait briefly and re-check
  sleep 5
  ok_unit2=0
  ok_port2=0
  if is_unit_active; then ok_unit2=1; fi
  if is_port_open; then ok_port2=1; fi
  ts2_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "[$ts2_utc] POST-RESTART unit_active=$ok_unit2 port_open=$ok_port2"

  [[ "$ok_unit2" -eq 1 && "$ok_port2" -eq 1 ]]
}

main "$@"
