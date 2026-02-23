# SQLite ↔ Azure AI Search — Memory Architecture & Flow

**Date:** 2026-02-23
**Context:** How the ClawBot brain skill stores, syncs, and queries memories

---

## Two-Store Architecture

```
SQLite (local)              Azure AI Search (cloud)
━━━━━━━━━━━━━━━             ━━━━━━━━━━━━━━━━━━━━━━━
ALL memories                COPY of all memories
+ FTS5 text index           + vector index (3072-dim)
                            + BM25 index
                            + semantic ranker

WRITE MASTER                READ REPLICA
Source of truth             Optimized for hybrid search
```

- SQLite is **never cleared** — it is the permanent source of truth
- Azure AI Search is a **searchable replica** rebuilt from SQLite
- If Azure is corrupted, run `memory_bridge.py sync --full` to rebuild from SQLite

---

## Pipeline: Session → SQLite → Azure → Hook

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: EXTRACTION (daily 4:15 PM ET / 20:15 UTC)         │
│                                                             │
│  Session JSONL files                                        │
│  (~/.openclaw/agents/main/sessions/*.jsonl)                 │
│       │                                                     │
│       ▼                                                     │
│  smart_extractor.py sweep                                   │
│       │                                                     │
│       ├─ Checks .extract_state.json (skip already-processed)│
│       ├─ Parses new session content                         │
│       ├─ Chunks if >14K chars                               │
│       ├─ Sends to GPT-5.2: "Extract facts + tags"           │
│       ├─ 5-Gate Pipeline:                                   │
│       │    ├─ Noise filter (score <0.3)                     │
│       │    ├─ Secrets filter (30+ patterns)                 │
│       │    ├─ Confidence filter (<0.4)                      │
│       │    ├─ Dedup filter (60% overlap)                    │
│       │    └─ Pivot detection                               │
│       └─ Stores via mem.py add                              │
│              │                                              │
│              ▼                                              │
│  ~/claude-memory/memory.db (SQLite)  ◄── SOURCE OF TRUTH   │
│                                                             │
│  Cost: ~$0.23/day (GPT-5.2 tokens)                         │
└─────────────────────────────────────────────────────────────┘
                    │
                    │  New memories in SQLite
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: AZURE SYNC (daily 4:35 PM ET / 20:35 UTC)         │
│                                                             │
│  memory_bridge.py sync                                      │
│       │                                                     │
│       ├─ Reads .sync_state.json (cursor = last synced ID)   │
│       ├─ Queries SQLite for NEW memories since cursor       │
│       ├─ Generates 3072-dim embeddings                      │
│       │    (text-embedding-3-large)                         │
│       ├─ Uploads to Azure AI Search index                   │
│       │    (clawbot-memory-store)                           │
│       ├─ Syncs any DELETIONS (removed from SQLite →         │
│       │    removed from Azure)                              │
│       └─ Updates .sync_state.json cursor                    │
│                                                             │
│  Cost: ~$0.001/day (embedding tokens only)                  │
└─────────────────────────────────────────────────────────────┘
                    │
                    │  Memories now searchable in Azure
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: HOOK INJECTION (every ClawBot turn)                │
│                                                             │
│  User sends message → before_agent_start hook fires         │
│       │                                                     │
│       ├─ Extract keywords from user message                 │
│       ├─ Embed query (text-embedding-3-large)               │
│       ├─ Query Azure AI Search (2s timeout)                 │
│       │    ├─ vector + BM25 + semantic ranking              │
│       │    ├─ SUCCESS → top 3-5 facts                       │
│       │    └─ TIMEOUT/ERROR → fallback to SQLite FTS5       │
│       │         ├─ SUCCESS → top 3-5 facts                  │
│       │         └─ ERROR → skip (no memory this turn)       │
│       └─ Return { prependContext: "<clawbot_memory>..." }   │
│                                                             │
│  Cost: ~$0.001/day (embedding for query only)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Fallback Chain

```
Hook fires on every turn:

  Try Azure AI Search (2s timeout)
       │
       ├─ SUCCESS → inject 3-5 facts (best quality: vector + semantic)
       │
       └─ FAIL/TIMEOUT
              │
              ├─ Try local SQLite FTS5
              │       │
              │       ├─ SUCCESS → inject 3-5 facts (text-match only)
              │       │
              │       └─ FAIL → skip gracefully (no memory this turn)
              │
              └─ Agent proceeds without memory context
```

---

## Data Flow: Write vs Read

### Writes (how memories get in)

```
Session JSONL → [Extraction cron] → SQLite → [Sync cron] → Azure AI Search
                   GPT-5.2            ▲
                                      │
                          mem.py add/delete (manual CLI)
```

- Only `smart_extractor.py` and `mem.py` write to SQLite
- Only `memory_bridge.py` writes to Azure (one-way push from SQLite)
- Azure is **never** written to directly

### Reads (how memories come out)

```
Hook query ──→ Azure AI Search (primary, hybrid search)
          └──→ SQLite FTS5 (fallback, text search)

SKILL.md deep recall ──→ Azure AI Search (with topic expansion via GPT-5.2)
                    └──→ SQLite FTS5 (fallback)
```

---

## Why Never Clear SQLite

| Scenario | What happens |
|----------|-------------|
| Azure is down/slow (>2s) | Hook falls back to SQLite FTS — still works |
| Azure index corrupted | Re-run `memory_bridge.py sync --full` to rebuild entirely from SQLite |
| Need to edit/delete a memory | Edit in SQLite via `mem.py`, next sync propagates to Azure |
| VM offline, no internet | SQLite still queryable locally |
| Disaster recovery | SQLite file is the backup — Azure can always be rebuilt from it |

**SQLite = write master, Azure AI Search = read replica.**

---

## Sync State Files

| File | Purpose | Updated by |
|------|---------|------------|
| `~/claude-memory/.extract_state.json` | Tracks which session files have been processed | `smart_extractor.py` |
| `~/claude-memory/.sync_state.json` | Cursor: last memory ID synced to Azure | `memory_bridge.py` |

These prevent re-processing. If either is deleted, the next run reprocesses everything (safe but slow).

---

## Key Design Decisions

1. **SQLite is never cleared** — permanent source of truth, enables full Azure rebuild
2. **One-way sync** — SQLite → Azure only. Azure is never the source of writes
3. **Cursor-based incremental sync** — only new/deleted memories since last run
4. **Separate extraction and sync schedules** — extraction (expensive, GPT-5.2) runs at 4:15 PM ET; sync (cheap, embeddings only) runs 20 min later at 4:35 PM ET
5. **Graceful degradation** — if any component fails, the system degrades but never crashes the gateway
