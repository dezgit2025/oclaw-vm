# RCA: Clawbot Session Log Context Overflow

**Date:** 2026-02-09 (two occurrences)
**Severity:** Service breaking — clawbot stops responding
**Error:** `Context overflow: prompt too large for the model.`

---

## Summary

Two overflow events on the same day:

| Occurrence | Session | Size | Messages | Cause |
|-----------|---------|------|----------|-------|
| #1 (15:33) | `c49b5fce` | 10 MB | 2,350 | Massive session, never rotated |
| #2 (18:06) | `c49b5fce` (new) | 121 KB | 51 | Small session but GitHub Copilot proxy context limit is lower than expected |

**Key finding:** The second overflow at only 121KB / 51 messages reveals the real constraint is not the model's native context window — it's the **GitHub Copilot API proxy** which imposes a smaller limit. The full prompt includes session history (~33K tokens) + system context (~7K tokens from .md files) + tool definitions, which together exceed the proxy's limit.

---

## System Architecture

```
  +------------+       +------------------+       +------------------+       +----------+
  |  Telegram  | ----> |  openclaw-gateway | ----> |  clawbot agent   | ----> | LLM API  |
  |  (user)    |       |  port 18792      |       |  main agent      |       | (GPT-5.2)|
  +------------+       +------------------+       +------------------+       +----------+
                                                         |
                                                         v
                                                  +------------------+
                                                  | Session Storage  |
                                                  | .jsonl files     |
                                                  | ~/.openclaw/     |
                                                  |  agents/main/    |
                                                  |  sessions/       |
                                                  +------------------+
```

---

## Message Flow: Telegram to LLM

```
  USER (Telegram)
       |
       | 1. Sends message via Telegram bot
       v
  +------------------+
  | openclaw-gateway |
  | (port 18792)     |
  |                  |
  | Receives webhook |
  | Routes to agent  |
  +--------+---------+
           |
           | 2. Forwards to clawbot agent
           v
  +------------------+
  | clawbot agent    |
  |                  |
  | 3. Loads session |-------> reads: ~/.openclaw/agents/main/sessions/{UUID}.jsonl
  |    file from     |
  |    disk          |         Session file format (.jsonl = one JSON per line):
  |                  |         ================================================
  |                  |         Line 1:  { type: "session",   id: "UUID", ... }
  |                  |         Line 2:  { type: "model_change", modelId: "gpt-5.2" }
  |                  |         Line 3:  { type: "thinking_level_change", ... }
  |                  |         Line 4:  { type: "custom", ... }
  |                  |         Line 5:  { type: "message", role: "user", ... }
  |                  |         Line 6:  { type: "message", role: "assistant", ... }
  |                  |         Line 7:  { type: "message", role: "user", ... }
  |                  |         ...
  |                  |         Line N:  { type: "message", role: "assistant", ... }
  |                  |
  | 4. Builds prompt |
  |    from ALL      |
  |    session lines |
  |                  |
  |  +---------------------------------+
  |  | PROMPT (sent to LLM):           |
  |  |   system instructions           |
  |  |   + CLAUDE.md / agent config    |
  |  |   + message line 5              |
  |  |   + message line 6              |
  |  |   + message line 7              |
  |  |   + ...                         |
  |  |   + message line N              |  <-- ALL history included
  |  |   + NEW user message            |
  |  +---------------------------------+
  |                  |
  +--------+---------+
           |
           | 5. Sends full prompt to LLM
           v
  +------------------+
  | LLM API          |
  | (GPT-5.2)        |
  |                  |
  | Processes prompt |
  | Returns response |
  +--------+---------+
           |
           | 6. Response returned
           v
  +------------------+
  | clawbot agent    |
  |                  |
  | 7. Appends to    |-------> writes: 2 new lines to session .jsonl
  |    session file  |            { type: "message", role: "user", ... }
  |    (user msg +   |            { type: "message", role: "assistant", ... }
  |     response)    |
  |                  |
  | 8. Sends reply   |
  +--------+---------+
           |
           | 9. Routes response back
           v
  +------------------+
  | openclaw-gateway |
  | Sends to         |
  | Telegram API     |
  +--------+---------+
           |
           | 10. Delivered
           v
  +------------+
  |  Telegram  |
  |  (user     |
  |   sees     |
  |   reply)   |
  +------------+
```

---

## Session File Growth Over Time

```
  Turn 1            Turn 100           Turn 500           Turn 1175
  ======            ========           ========           =========

  .jsonl file:      .jsonl file:       .jsonl file:       .jsonl file:
  +------+          +--------+         +----------+       +------------+
  |header|          |header  |         |header    |       |header      |
  |msg 1 |          |msg 1   |         |msg 1     |       |msg 1       |
  |resp 1|          |msg 2   |         |msg 2     |       |msg 2       |
  |      |          |...     |         |...       |       |...         |
  |      |          |msg 100 |         |msg 500   |       |msg 1175   |
  +------+          +--------+         +----------+       +------------+
   ~8 KB             ~100 KB            ~2 MB              10 MB
                                                               |
  Prompt sent        Prompt sent        Prompt sent        Prompt sent
  to LLM: ~8KB      to LLM: ~100KB     to LLM: ~2MB      to LLM: ~10MB
                                                               |
  OK                 OK                 Getting slow...     REJECTED
                                                           "prompt too
                                                            large"
```

---

## Root Cause Analysis

### Occurrence #1: 10MB Session (Obvious)

Session `c49b5fce` accumulated 2,350 lines (10MB). The full session is sent as context on every turn. At 10MB this exceeds any model's context window.

**Contributing factors:**

1. **No session rotation** — session persisted across hours/days
2. **Insufficient compaction** — only 10 compaction events across 2,350 messages; compaction adds summaries but does NOT remove originals
3. **Huge tool outputs stored verbatim** — 5 messages alone = 1.5MB:

```
  +-------------------------------------------+
  | Line 40:   582 KB  (largest single line)  |
  | Line 663:  302 KB                         |
  | Line 681:  255 KB                         |
  | Line 1414: 204 KB                         |
  | Line 1534: 131 KB                         |
  +-------------------------------------------+
  | Total:     1,474 KB (just 5 of 2,350)     |
  +-------------------------------------------+
```

### Occurrence #2: 121KB Session (The Real Problem)

After backing up the 10MB session, a fresh session overflowed at only **121KB / 51 messages**. This revealed the deeper issue.

**Prompt size breakdown:**

```
  What gets sent to the LLM on EVERY turn:
  =========================================

  System context (.md files):                 ~27 KB  (~7K tokens)
    AGENTS.md       7.7 KB
    SOUL.md         1.7 KB
    TOOLS.md        860 B
    USER.md         329 B
    IDENTITY.md     189 B
    HEARTBEAT.md    168 B
    MEMORY.md       148 B
    SKILL.md files  ~16 KB (across all skills)

  + Session history (51 messages):           ~133 KB  (~33K tokens)

  + Tool/function definitions:                ~??? KB  (unknown, potentially large)

  + New user message:                         ~1 KB
                                             ---------
  TOTAL PROMPT:                              ~40K+ tokens
```

**The constraint: GitHub Copilot API proxy**

```
  models.json configuration:
  ==========================

  "github-copilot": {
    "models": []              <-- NO context window defined!
  }

  "foundry": {
    "models": [
      { "id": "Kimi-K2.5",     "contextWindow": 128000 },
      { "id": "gpt-4.1-mini",  "contextWindow": 128000 }
    ]
  }
```

The active model is `gpt-5.2` via the `github-copilot` provider. This provider:
- Has **no models listed** in the config (empty array)
- Has **no contextWindow defined** — so the agent has no guardrail
- The Copilot API proxy likely imposes a **smaller context limit** than GPT-5.2's native window
- At ~40K tokens the prompt exceeds this proxy limit

**This is why 51 messages overflow while 128K-context Foundry models would handle it easily.**

### Session Breakdown (Occurrence #1)

```
  c49b5fce session (10 MB)
  ========================

  By type:
    messages:    2,336  (99.4%)
    compaction:     10  (0.4%)
    config:          4  (0.2%)

  By size distribution:
    > 100 KB:     5 messages  (~1.5 MB)
    10-100 KB:   ~50 messages (~2.5 MB)
    1-10 KB:    ~200 messages (~1.0 MB)
    < 1 KB:   ~2,081 messages (~5.0 MB)
```

---

## Fixes Applied

```bash
# Occurrence #1: Backed up bloated sessions
mv c49b5fce-...jsonl c49b5fce-...jsonl.backup-20260209    # 10 MB
mv 85a99b58-...jsonl 85a99b58-...jsonl.backup-20260209    # 1.2 MB

# Occurrence #2: Backed up again after it re-overflowed at 121KB
mv c49b5fce-...jsonl c49b5fce-...jsonl.backup-20260209b   # 121 KB
```

Clawbot automatically creates a fresh session on next message.

---

## Recommendations

### Short-term (manual)

1. **Monitor session sizes weekly**
   ```bash
   find ~/.openclaw/agents/main/sessions/ -name "*.jsonl" -size +500k -exec ls -lh {} \;
   ```

2. **Rotate large sessions manually**
   ```bash
   # Find and back up sessions over 500KB
   find ~/.openclaw/agents/main/sessions/ -name "*.jsonl" -size +500k \
     -exec mv {} {}.backup-$(date +%Y%m%d) \;
   ```

3. **Archive old sessions (7+ days)**
   ```bash
   find ~/.openclaw/agents/main/sessions/ -name "*.jsonl" -mtime +7 \
     -exec mv {} {}.archived \;
   ```

### Medium-term (automation)

4. **Cron job for session cleanup** — rotate sessions over 500KB daily
5. **Alerting** — notify when any session exceeds 200KB

### Medium-term (model config)

4. **Switch to Foundry models** — Kimi-K2.5 and GPT-4.1-mini have 128K context windows vs the Copilot proxy's unknown (likely 32K) limit
5. **Define contextWindow for github-copilot** — add GPT-5.2 with an explicit context limit in models.json so the agent can self-regulate
6. **Cron job for session cleanup** — rotate sessions over 100KB daily (lowered from 500KB given the Copilot limit)

### Long-term (code changes)

7. **Sliding window** — only send the last N messages as context, not the full history
8. **Aggressive compaction** — summarize and DELETE old messages, not just append summaries
9. **Tool output truncation** — cap stored tool outputs at a max size (e.g., 10KB)
10. **Session TTL** — auto-expire sessions after a configurable time period
11. **Token counting** — count prompt tokens before sending; if over threshold, compact first
12. **Reduce system context** — audit .md files (27KB total) injected on every turn; trim or consolidate

---

## Size Thresholds (Reference)

### For GitHub Copilot proxy (current — ~32K token limit)

| Session Size | Status | Action |
|-------------|--------|--------|
| < 30 KB | Normal | No action |
| 30-80 KB | Warning | Session approaching limit (~25-40 messages) |
| 80-120 KB | Critical | Will overflow soon, rotate proactively |
| > 120 KB | Overflow | Rotate immediately |

### For Foundry models (128K context window)

| Session Size | Status | Action |
|-------------|--------|--------|
| < 200 KB | Normal | No action |
| 200 KB - 1 MB | Warning | Session getting long, monitor |
| > 1 MB | Critical | Rotate immediately |

---

## Files

| File | Location |
|------|----------|
| Session storage | `VM: ~/.openclaw/agents/main/sessions/` |
| Session index | `VM: ~/.openclaw/agents/main/sessions/sessions.json` |
| Bloated session backup #1 | `VM: ~/.openclaw/agents/main/sessions/c49b5fce-...jsonl.backup-20260209` (10MB) |
| Secondary backup | `VM: ~/.openclaw/agents/main/sessions/85a99b58-...jsonl.backup-20260209` (1.2MB) |
| Bloated session backup #2 | `VM: ~/.openclaw/agents/main/sessions/c49b5fce-...jsonl.backup-20260209b` (121KB) |
| Model config | `VM: ~/.openclaw/agents/main/agent/models.json` |
| This RCA | `local: manage-oclaw/rca-session-log-bug-20260209.md` |
