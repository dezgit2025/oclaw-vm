# Mem0 Integration Options for Session Log Overflow Fix

**Date:** 2026-02-09
**Problem:** Session .jsonl files grow unbounded (10 MB / 2,350 entries) causing context overflow
**Goal:** Use mem0 as a memory manager so sessions can be rotated without losing context

---

## Background

The session log analysis (`session-log-analysis-doc.md`) revealed:
- 99.4% of the file is `message` entries (2,336 of 2,350)
- Tool results are the largest entries (568 KB max, top 5 = 1.4 MB)
- Compaction appends summaries but never deletes originals (+223 KB)
- GitHub Copilot proxy overflows at ~32K tokens (~80-120 KB session)
- Foundry models (128K context) overflow at ~1 MB

Mem0 (`@mem0/openclaw-mem0`) is an OpenClaw plugin that provides:
- **Auto-recall:** injects relevant memories before each agent turn
- **Auto-capture:** extracts key facts after each agent turn
- **5 agent tools:** memory_search, memory_list, memory_store, memory_get, memory_forget
- **Dual scope:** session (short-term) + user (long-term) memories
- **Two modes:** Mem0 Cloud (platform) or self-hosted open-source

---

## 5 Integration Options (Easy → Hard)

### Option 1: Install mem0 plugin with Mem0 Cloud (easiest)

**Complexity:** Low — config change only, no infrastructure

```
  Current (no memory)                 With Mem0 Cloud
  ====================                ================

  Session .jsonl grows forever        Mem0 extracts key facts
  10MB → overflow                     Session can be rotated freely
                                      Memories persist in Mem0 Cloud

  openclaw.json:
  "openclaw-mem0": {
    "enabled": true,
    "config": {
      "apiKey": "${MEM0_API_KEY}",     ← requires Mem0 account
      "userId": "desazure"
    }
  }
```

**What it solves:** Agent retains knowledge across session rotations. You can aggressively rotate sessions (every 50 messages or 80 KB) without losing context — mem0's auto-recall injects relevant memories before each turn.

**What it doesn't solve:** Doesn't shrink the active session itself. Still need GC/rotation.

**Steps:** `openclaw plugins install @mem0/openclaw-mem0` → add config → restart gateway.

---

### Option 2: Install mem0 plugin with self-hosted OSS mode via existing Foundry proxy (medium-easy)

**Complexity:** Medium-low — uses existing infrastructure, zero API keys

```
  OpenClaw Agent
       |
       v
  mem0 plugin (auto-recall + auto-capture)
       |
       |  LLM + Embeddings
       v
  Foundry MI Proxy (127.0.0.1:18791)    ← already running!
       |
       v
  Azure AI Foundry (gpt-4.1-mini)
       |
  Vector Store: Qdrant embedded (local file, no Docker)
  History: SQLite (~/.mem0/history.db)
```

**Config:**

```json
"openclaw-mem0": {
  "enabled": true,
  "config": {
    "mode": "open-source",
    "userId": "desazure",
    "oss": {
      "llm": { "provider": "openai", "config": {
        "model": "gpt-4.1-mini",
        "openai_base_url": "http://127.0.0.1:18791/v1",
        "api_key": "not-needed"
      }},
      "embedder": { "provider": "openai", "config": {
        "model": "text-embedding-3-small",
        "openai_base_url": "http://127.0.0.1:18791/v1",
        "api_key": "not-needed"
      }},
      "vectorStore": { "provider": "qdrant", "config": {
        "path": "/home/desazure/.openclaw/mem0/qdrant_data",
        "on_disk": true
      }}
    }
  }
}
```

**Resource cost:** < 300 MB RAM, no Docker, no external API keys. Qdrant runs embedded in-process.

**Blocker:** Need to verify that your Azure Foundry deployment has an embeddings model (`text-embedding-3-small`) deployed. If not, you'd need to deploy one or use Ollama for embeddings only.

---

### Option 3: Mem0 + aggressive session rotation cron (medium)

**Complexity:** Medium — combines mem0 (option 1 or 2) with automated session management

```
  Current flow (broken):
  ======================
  Session grows → 10MB → overflow → manual backup → fresh session

  Fixed flow:
  ===========
  Session grows → mem0 captures facts continuously
       |
       v
  Cron (every 30 min):
    if session > 80KB:
      1. mem0 already has the important facts
      2. Archive session → .backup
      3. Fresh session created on next message
      4. mem0 auto-recall injects relevant memories
       |
       v
  Session never exceeds ~100KB
  Agent never loses important context
```

**What you'd build:**

1. Install mem0 (option 1 or 2)
2. Lower the session GC threshold from 5 MB → 80 KB (for Copilot proxy)
3. Add a cron job that checks session sizes every 30 min and rotates any over 80 KB
4. Trust mem0's auto-recall to bring back relevant context in the fresh session

**This directly solves:** Both the 10 MB overflow AND the 121 KB/51 message overflow.

---

### Option 4: Mem0 + custom compaction that actually deletes old messages (medium-hard)

**Complexity:** Medium-hard — requires writing a compaction script

```
  Current compaction (broken):          Fixed compaction:
  ============================          =================

  Session: 2,350 lines                  Session: 2,350 lines
       |                                      |
       v                                      v
  Compact: append summary               1. mem0.add(last 200 messages)
  File: 2,350 + 1 summary = 2,351           → extracts & stores facts
       |                                      |
       v                                      v
  BIGGER! (223KB of summaries added)    2. Rewrite .jsonl:
                                           - Keep header (4 lines)
                                           - Keep last 50 messages
                                           - Delete everything else
                                              |
                                              v
                                        3. File: 54 lines (~50KB)
                                           Agent context = recent history
                                           + mem0 recalled memories
```

**What you'd build:**

- A Python script (`session_compact.py`) that:
  1. Reads the current session .jsonl
  2. Feeds older messages to mem0 for fact extraction
  3. Rewrites the file keeping only the header + last N messages
  4. Runs via cron or hook when token count exceeds a threshold

**This is the most complete solution** — it keeps sessions small while preserving all important knowledge in mem0.

---

### Option 5: Full mem0-backed sliding window with tool output truncation (hardest)

**Complexity:** Hard — requires OpenClaw plugin development or upstream contribution

```
  Every agent turn:
  =================

  1. BEFORE turn:
     +------------------------------------------+
     | System prompt (~7K tokens)               |
     | + mem0 recalled memories (top 5-10)      |  ← long-term context
     | + last 20 messages (sliding window)       |  ← short-term context
     | + new user message                        |
     +------------------------------------------+
     Total: ~15-20K tokens (fits in 32K Copilot window)

  2. DURING turn:
     Tool outputs truncated at 10KB before storage
     (was: 568KB stored verbatim)

  3. AFTER turn:
     mem0 auto-capture extracts facts
     Old messages beyond window are NOT sent to LLM
     but remain in .jsonl for audit

  Architecture:
  =============

  +------------------+     +------------------+     +------------------+
  | Session .jsonl   |     | mem0 memories    |     | LLM prompt       |
  | (full history,   |     | (extracted facts,|     | (bounded size,   |
  |  audit log)      |     |  vector indexed) |     |  always fits)    |
  +------------------+     +------------------+     +------------------+
        |                        |                        ^
        | write all              | auto-capture           | auto-recall
        v                        v                        | + sliding window
  Append-only log          Qdrant + SQLite          Sent to LLM API
  (can be archived)        (persistent)             (max ~25K tokens)
```

**What you'd build/modify:**

1. **Sliding window** in the prompt builder — only include last N messages, not full history
2. **Tool output truncation** — cap at 10 KB before writing to session file
3. **mem0 auto-recall** — injects relevant long-term memories to compensate for the window
4. **mem0 auto-capture** — extracts facts from every turn so nothing important is lost
5. **Token pre-flight check** — count tokens before sending, compact if needed
6. **Provider-aware limits** — different window sizes for Copilot (32K) vs Foundry (128K)

**This eliminates the overflow problem entirely** — the prompt is always bounded regardless of session length. The .jsonl file can still grow as an audit log, but it's never sent in full to the LLM.

---

## Comparison

| # | Approach | Effort | Overflow Fix | Memory Retention | Dependencies |
|---|----------|--------|:------------:|:----------------:|--------------|
| 1 | Mem0 Cloud plugin | Config only | Partial (needs rotation) | Full | Mem0 API key ($) |
| 2 | Mem0 OSS + Foundry proxy | Low | Partial (needs rotation) | Full | None (uses existing infra) |
| 3 | Mem0 + rotation cron | Medium | Yes | Full | Mem0 + cron script |
| 4 | Mem0 + real compaction | Medium-hard | Yes | Full | Mem0 + compaction script |
| 5 | Sliding window + truncation | Hard | Complete | Full | Mem0 + OpenClaw modifications |

---

## Recommendation

Start with **Option 2** (zero cost, uses your existing Foundry proxy) then add **Option 3** (rotation cron) once mem0 is capturing memories reliably. That gives you full overflow protection with minimal effort.

---

## Self-Hosted Architecture (Option 2 Detail)

```
  oclaw2026linux (Ubuntu)
  +------------------------------------------------------------+
  |  OpenClaw v2026.2.9 (Node.js)                             |
  |       |                                                     |
  |       v                                                     |
  |  mem0 plugin (@mem0/openclaw-mem0)                         |
  |   - Auto-recall: injects memories before each turn         |
  |   - Auto-capture: extracts facts after each turn           |
  |   - 5 tools: search, list, store, get, forget              |
  |       |                                                     |
  |       v                                                     |
  |  mem0ai (Node.js library, OSS mode)                        |
  |   - LLM: openai provider → http://127.0.0.1:18791/v1      |
  |   - Embedder: openai provider → http://127.0.0.1:18791/v1  |
  |   - Vector Store: Qdrant embedded (local path, on_disk)    |
  |   - History: SQLite (~/.mem0/history.db)                   |
  |       |                                                     |
  |       v                                                     |
  |  Foundry MI Proxy (port 18791, already running)            |
  |   - Strips foundry/ prefix from model names                |
  |   - Injects Managed Identity token via IMDS                |
  |   - Normalizes reasoning_content → content                 |
  |       |                                                     |
  |       v                                                     |
  |  Azure AI Foundry                                          |
  |   - gpt-4.1-mini (LLM for fact extraction)                |
  |   - text-embedding-3-small (embeddings) *needs deployment  |
  +------------------------------------------------------------+
```

**Resource requirements:**

| Component | CPU | RAM | Disk |
|-----------|-----|-----|------|
| mem0 library | Negligible | ~50 MB | ~20 MB |
| Qdrant embedded | Negligible | ~100-200 MB | Grows with data |
| SQLite history | Negligible | Negligible | Grows with data |
| **Total** | **< 0.5 CPU** | **~150-300 MB** | **< 100 MB initially** |

Zero API keys stored on the VM. No Docker needed.

---

## How mem0 Plugin Works (Technical)

```
  BEFORE each agent turn (auto-recall):
  ======================================

  User sends message
       |
       v
  mem0 searches memories (both scopes):
    - Long-term: user_id only (cross-session facts)
    - Session: user_id + run_id (current conversation)
       |
       v
  Injects into system prompt:
    <relevant-memories>
    Long-term memories:
    - User prefers Kimi-K2.5 for research tasks [preference]
    - VM uses managed identity for Azure auth [technical]
    Session memories:
    - Currently debugging foundry proxy model name issue [project]
    </relevant-memories>
       |
       v
  Agent processes message with full context


  AFTER each agent turn (auto-capture):
  ======================================

  Agent responds
       |
       v
  mem0 receives last 10 messages
       |
       v
  Sends to Mem0's LLM (gpt-4.1-mini):
    "Extract important facts from this exchange"
       |
       v
  Mem0 decides:
    - ADD new facts
    - UPDATE existing facts (dedup/merge)
    - DELETE stale facts
    - NOOP (nothing worth storing)
       |
       v
  Facts stored in Qdrant (vector indexed)
  + SQLite (audit history)
```

---

## Prerequisite Check

Before implementing any option, verify:

```bash
# 1. OpenClaw version supports plugins
ssh oclaw "npm list -g | grep openclaw"
# Need: v2026.2.x+

# 2. Check if embeddings model is deployed on Azure Foundry
# (needed for Option 2 OSS mode)
ssh oclaw "curl -s http://127.0.0.1:18791/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{\"model\":\"text-embedding-3-small\",\"input\":\"test\"}' | head -c 200"

# 3. Check available disk space
ssh oclaw "df -h /home/desazure"

# 4. Check available RAM
ssh oclaw "free -h"
```

---

## Related Documents

| Document | Path |
|----------|------|
| Session log analysis | `manage-oclaw/session-log-analysis-doc.md` |
| RCA: context overflow | `manage-oclaw/rca-session-log-bug-20260209.md` |
| Foundry proxy fix | `manage-oclaw/fix-foundry-model-proxy.md` |
| Context overflow fix | `manage-oclaw/clawbot-context-overflow-fix.md` |
| mem0 plugin source | `github.com/mem0ai/mem0/tree/main/openclaw` |
| mem0 OSS docs | `docs.mem0.ai/open-source/overview` |
