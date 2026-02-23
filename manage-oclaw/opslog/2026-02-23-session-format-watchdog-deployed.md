# Session Format Watchdog Deployed

**Date:** 2026-02-23
**Severity:** Improvement — prevents silent memory pipeline breakage after openclaw updates
**Affected:** Memory extraction pipeline (`smart_extractor.py sweep`)

## What Changed

Deployed `session_format_watchdog.py` to the oclaw VM to detect session log format changes (e.g. v3 to v4) before they silently break the memory extraction pipeline. This was motivated by the v2 to v3 format mismatch bug that caused 0 candidates to be extracted from all sessions until a ~180-line v3 parser was added.

## Problem

When openclaw gets `npm update`'d, the session `.jsonl` format can change silently. The `smart_extractor.py` parser only recognizes specific event types and field schemas. A format bump (like v2 to v3) causes the extractor to return 0 candidates instead of erroring — silent data loss for the memory system.

## Solution

A lightweight Python watchdog script (`session_format_watchdog.py`, ~300 lines, stdlib-only) that runs via cron 5 minutes before the daily extraction sweep. It performs three checks:

1. **Version check** — Reads the newest session file's first line, extracts the `version` field, compares against expected version (currently 3)
2. **Event type scan** — Scans first 50 lines for unknown event types not in the known set: `{session, message, model_change, thinking_level_change, custom, compaction}`
3. **Canary extraction** — Optionally runs `smart_extractor.py canary` to test-extract from the newest session (skipped for now — canary subcommand not yet implemented)

## Files Deployed

| File | VM Path |
|------|---------|
| Watchdog script | `~/.openclaw/workspace/skills/clawbot-memory/session_format_watchdog.py` |
| State file | `~/.local/state/openclaw/session-format-watchdog.state` |
| Log dir | `~/.openclaw/logs/session-format-watchdog/` |
| Source (laptop) | `soul/hooks/clawbot-memory/session_format_watchdog.py` |

## Cron Job

```
10 20 * * * source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && python3 session_format_watchdog.py >> ~/.openclaw/logs/session-format-watchdog/cron.log 2>&1
```

Runs at 20:10 UTC daily — 5 minutes before extraction sweep (20:15 UTC).

## Full Cron Order (Memory Pipeline)

```
20:10 UTC  session_format_watchdog.py     (validate format)
20:15 UTC  smart_extractor.py sweep       (extract facts)
20:35 UTC  memory_bridge.py sync          (push to Azure AI Search)
```

## Alert Conditions

| Condition | Severity | Exit Code |
|-----------|----------|-----------|
| Version mismatch | CRITICAL | 2 |
| Canary extraction 0 candidates | CRITICAL | 2 |
| Unknown event types | WARNING | 1 |
| Session header unparseable | CRITICAL | 2 |
| All checks pass | OK | 0 |

## Test Results

```
[2026-02-23T07:27:10+00:00] INFO Checking session: 5e862d5b-f21c-4086-a5cd-a120cc06f2ea.jsonl
[2026-02-23T07:27:10+00:00] INFO Version OK: 3
[2026-02-23T07:27:10+00:00] INFO Event types OK: ['custom', 'message', 'model_change', 'session', 'thinking_level_change']
[2026-02-23T07:27:10+00:00] INFO Canary extraction skipped (canary subcommand not supported)
[2026-02-23T07:27:10+00:00] INFO Watchdog complete — exit 0, consecutive_failures=0
```

## State File (after test)

```json
{
  "expected_version": 3,
  "last_checked": "2026-02-23T07:27:10+00:00",
  "last_version_seen": 3,
  "known_event_types": ["compaction", "custom", "message", "model_change", "session", "thinking_level_change"],
  "unknown_types_seen": [],
  "canary_result": "skipped",
  "canary_detail": "canary subcommand not supported",
  "consecutive_failures": 0,
  "last_session_file": "5e862d5b-f21c-4086-a5cd-a120cc06f2ea.jsonl",
  "last_session_id": "5e862d5b-f21c-4086-a5cd-a120cc06f2ea"
}
```

## CLAUDE.md Updates

- Added `session_format_watchdog.py` to cron jobs table
- Added post-update workflow: run `--force` after any `npm update`
- Added quick check command for state file

## Quick Checks

```bash
# Watchdog state
ssh oclaw "cat ~/.local/state/openclaw/session-format-watchdog.state"

# Today's log
ssh oclaw "cat ~/.openclaw/logs/session-format-watchdog/$(date -u +%Y-%m-%d).log"

# Force revalidation (after npm update)
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory && python3 session_format_watchdog.py --force"
```

## Gotchas

- **Run `--force` after any `npm update`** — The cron schedule only checks once daily; a mid-day update could break the evening extraction sweep before the watchdog catches it
- **Canary subcommand not yet implemented** — The third check (end-to-end test extraction) is skipped until `smart_extractor.py canary` is added
- **Exit code 1 (WARNING) does not block extraction** — Unknown event types are logged but the pipeline still runs. Only exit code 2 (CRITICAL) indicates a format that will definitely break extraction

## TODO

- Add `canary` subcommand to `smart_extractor.py` for end-to-end format validation
- Consider blocking extraction sweep if watchdog exits non-zero (gate the pipeline)
