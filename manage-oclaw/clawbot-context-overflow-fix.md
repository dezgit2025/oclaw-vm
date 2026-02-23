# Clawbot Context Overflow: Root Cause & Fix

## The Error

```
Context overflow: prompt too large for the model.
Try again with less input or a larger-context model.
```

## What Happened

Session `c49b5fce` grew to **10MB / 2,350 lines** — the entire conversation history was being sent as the prompt to the LLM, exceeding its context window limit.

## Root Cause

```
  Each new message to clawbot
          |
          v
  +-------------------+
  | Session .jsonl     |     <-- Every message appended here
  | Line 1: msg        |
  | Line 2: response   |
  | Line 3: msg        |
  | ...                |
  | Line 2350: msg     |     <-- 10MB of conversation history
  +-------------------+
          |
          v
  +-------------------+
  | LLM API Call       |
  | prompt = entire    |     <-- ALL 2,350 lines sent as context
  |   session history  |
  +-------------------+
          |
          v
  +-------------------+
  | REJECTED           |     <-- Exceeds model's context window
  | "prompt too large" |
  +-------------------+
```

The clawbot agent appends every message exchange to a single `.jsonl` session file. When the session runs long enough, the accumulated history exceeds the model's token limit (~200K tokens for most Claude models). A 10MB JSONL file easily blows past this.

## Why It Grows

```
  Session Start                    After Hours of Use
  =============                    ==================

  +--------+                       +--------+
  | 7.5 KB |  (normal)             | 10 MB  |  (overflow!)
  | ~20    |  lines                | ~2350  |  lines
  +--------+                       +--------+

  Typical session: 7-15 KB          This session: 10,240 KB
  Lives for: ~30 min                Lived for: hours/days
  Messages: 10-30                   Messages: 2,350
```

Contributing factors:
- Long-running sessions that aren't rotated
- Large tool outputs (file contents, API responses) stored in history
- System prompts + CLAUDE.md injected on every turn
- No automatic truncation or summarization

## The Fix (What We Did)

```
  Before                              After
  ======                              =====

  sessions/                           sessions/
    c49b5fce.jsonl  (10MB)  --mv-->     c49b5fce.jsonl.backup-20260209
    85a99b58.jsonl  (1.2MB) --mv-->     85a99b58.jsonl.backup-20260209
    ...normal files...                  ...normal files... (all < 82KB)
```

1. Identified the bloated session: `c49b5fce` at 10MB
2. Backed it up: renamed to `.backup-20260209`
3. Also backed up secondary large session: `85a99b58` at 1.2MB
4. Clawbot will create a fresh session on next message

## Prevention

### Monitor session sizes

Check for sessions growing too large:

```bash
# On the VM - find sessions over 500KB
find ~/.openclaw/agents/main/sessions/ -name "*.jsonl" -size +500k -exec ls -lh {} \;
```

### Periodic cleanup of old sessions

```bash
# Archive sessions older than 7 days
find ~/.openclaw/agents/main/sessions/ -name "*.jsonl" -mtime +7 -exec mv {} {}.archived \;
```

### Size thresholds

| Size | Status | Action |
|------|--------|--------|
| < 50 KB | Normal | No action needed |
| 50-200 KB | Large | Session is getting long, consider starting fresh |
| 200 KB - 1 MB | Warning | Will likely overflow soon |
| > 1 MB | Critical | Move aside immediately, start fresh |

## Session File Location

```
/home/desazure/.openclaw/agents/main/sessions/
```

Each session is a `.jsonl` file (one JSON object per line) named with a UUID.
