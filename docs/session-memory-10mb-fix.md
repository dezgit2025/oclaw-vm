# session-memory-10mb-fix

Date: 2026-02-09

## Problem
OpenClaw session logs (JSONL) can grow without bound. The agent was building prompts from *all* session history each turn, which eventually triggered:

- **Error:** `Context overflow: prompt too large for the model.`

In the incident RCA, one session file grew to ~10MB / ~2,350 lines, causing subsequent LLM calls to fail.

## Goal
Add a pragmatic safety valve:

- If any session file is **> 5MB**:
  - create a backup
  - truncate **oldest entries** so the session file returns to about **3MB**
- Run automatically **daily at 8pm ET**
- Provide rollback steps.

## What was implemented

### A) Session GC / truncation script
Created:

- `/home/desazure/.openclaw/workspace/manage-oclaw/session_gc.py`

Behavior:

- Scans: `~/.openclaw/agents/main/sessions/*.jsonl`
- If a `.jsonl` file exceeds **--max-mb** (default **5.0MB**):
  1) **Backs it up** to a sibling file:
     - `<session>.jsonl.backup-YYYYMMDD-HHMMSS` (UTC timestamp)
  2) Rewrites the original file so it fits within **--target-mb** (default **3.0MB**)

Truncation strategy:

- Keeps the initial **header block** (the first contiguous non-`{"type":"message"}` lines at the start: session/config/model change lines)
- Keeps the **newest message lines** from the end until the size target is reached
- If the header alone exceeds the target, it keeps the header only (best effort)
- If a single message line is larger than the remaining budget, it will keep that one line (cannot split JSONL safely without partial-line surgery)

### B) Runner wrapper with logging
Created:

- `/home/desazure/.openclaw/workspace/manage-oclaw/run_session_gc.sh`

Behavior:

- Runs `session_gc.py`
- Appends output to:
  - `~/.openclaw/logs/session-gc.log`

### C) Automated daily run at 8pm ET (Linux crontab)
Installed user crontab entry:

```cron
# OpenClaw session log GC (backup >5MB, truncate to ~3MB)
TZ=America/New_York
0 20 * * * /home/desazure/.openclaw/workspace/manage-oclaw/run_session_gc.sh
```

### D) OpenClaw reminder cron (optional / legacy)
An OpenClaw cron reminder job was also created earlier (not required if Linux cron is used):

- Job id: `044596bd-968f-4772-b2ec-13c1ed4acee3`

This job posts a reminder to run the script manually.

## Test performed
A synthetic JSONL session file was generated (~471KB) and the script was run with low thresholds to force truncation.

Result:

- Original: **471,101 bytes**
- New: **19,716 bytes**
- Backup created: `testsession.jsonl.backup-20260209-182220`
- Header preserved: `session`, `model_change` remained at the top

## Rollback options

### Option 1 — Disable the schedule (keep scripts, stop running)
Edit user crontab:

```bash
crontab -e
```

Delete these lines:

```cron
TZ=America/New_York
0 20 * * * /home/desazure/.openclaw/workspace/manage-oclaw/run_session_gc.sh
```

If you are sure you don’t use user-crontab for anything else, you can remove the entire crontab:

```bash
crontab -r
```

### Option 2 — Restore a single truncated session from its backup
Backups are created alongside the session file:

- `<session>.jsonl.backup-YYYYMMDD-HHMMSS`

Restore example:

```bash
cd ~/.openclaw/agents/main/sessions
ls -la *.backup-*

mv <session>.jsonl <session>.jsonl.truncated
mv <session>.jsonl.backup-YYYYMMDD-HHMMSS <session>.jsonl
```

### Option 3 — Disable + remove scripts + logs

```bash
# 1) disable schedule
crontab -e

# 2) remove scripts
rm -f /home/desazure/.openclaw/workspace/manage-oclaw/session_gc.py
rm -f /home/desazure/.openclaw/workspace/manage-oclaw/run_session_gc.sh

# 3) optional: remove logs
rm -f ~/.openclaw/logs/session-gc.log
```

### Option 4 — Keep only the OpenClaw reminder cron
- Remove Linux crontab entry (Option 1)
- Keep scripts for manual use
- Keep OpenClaw cron reminder enabled (or disable it if not wanted)

## Notes / limitations
- This is a mitigation, not a full architectural fix. A long-term fix would be a sliding window, aggressive compaction that *replaces* history, tool-output truncation, and token counting prior to calling the model.
