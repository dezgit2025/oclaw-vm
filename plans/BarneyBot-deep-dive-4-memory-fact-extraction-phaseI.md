# BarneyBot Brain System — Architecture Diagram

**Date:** 2026-02-23
**Related:** [ClawBot Memory System Deployed](2026-02-23-clawbot-memory-system-deployed.md), [Phase II Plan](2026-02-23-memory-enhancement-phaseII-plan.md)

---

## Pipeline Summary

```
Conversations → GPT-5.2 extracts facts → JSON with tags → SQLite → sync → Azure embeds with vectors
```

Each stage has ONE job. No stage does another stage's work.

---

```
                         ┌──────────────────────────────────────┐
                         │          BARNEYBOT BRAIN v1          │
                         └──────────────────────────────────────┘


  ═══════════════════════════════════════════════════════════════════════════════════
  STAGE 1: UNDERSTANDING                        "What is worth remembering?"
  Concern: Turn messy conversations into clean, atomic facts
  Runs: Daily 20:15 UTC via cron
  ═══════════════════════════════════════════════════════════════════════════════════

  ╔═══════════════════╗
  ║  Telegram / Web   ║     ┌──────────────────────────────────────────────────┐
  ║   Conversations   ║     │  smart_extractor.py sweep                        │
  ║                   ║     │                                                  │
  ║  Raw session logs ║────▶│  LLM: GPT-5.2 (Azure OpenAI)                    │
  ║  (~/.openclaw/    ║     │                                                  │
  ║   agents/main/    ║     │  Job: READ conversations, EXTRACT facts          │
  ║   sessions/)      ║     │                                                  │
  ╚═══════════════════╝     │  Input:  "[user]: Remove Bastion, saves $138/mo" │
  ║                         │  Output: {                                       │
  ║  Messy, long,           │    "fact": "Removed Azure Bastion — saves        │
  ║  full of noise,         │            ~$138/month. Tailscale replaces        │
  ║  greetings,             │            all SSH access",                       │
  ║  debug output,          │    "tags": ["type:decision",                     │
  ║  code blocks            │            "domain:infrastructure",              │
  ║                         │            "decided:2026-02-22",                 │
  ╚═════════════════════╝   │            "confidence:high"],                   │
                            │    "confidence": 0.95                            │
                            │  }                                               │
                            │                                                  │
                            │  Then: 5-gate quality filter                     │
                            │     ├─ noise gate     (skip greetings/small talk)│
                            │     ├─ secrets gate   (block API keys/passwords) │
                            │     ├─ confidence gate (drop if < 0.6)           │
                            │     ├─ dedup gate     (skip if already stored)   │
                            │     └─ pivot detection (flag contradictions)     │
                            └──────────────────┬───────────────────────────────┘
                                               │
                            DOES NOT: store vectors, embed anything, search
                            ONLY: understands language → produces JSON facts
                                               │
                                               ▼

  ═══════════════════════════════════════════════════════════════════════════════════
  STAGE 2: STORAGE                              "Save the facts reliably"
  Concern: Durable, local, instant writes — plain text, no vectors
  Runs: Immediately after extraction
  ═══════════════════════════════════════════════════════════════════════════════════

  ┌────────────────────────────────────────────────────────────────────────────┐
  │                  SQLite — Source of Truth (WRITE STORE)                    │
  │                  ~/.claude-memory/memory.db                                │
  │                                                                            │
  │  mem.py add "Removed Azure Bastion..." -p oclaw -t "type:decision,..."    │
  │                                                                            │
  │  What it stores (PLAIN TEXT, no vectors, no embeddings):                   │
  │  ┌──────────┬──────────────────────────────────────────────────────────┐   │
  │  │ id       │ mem_4d8cda41 (SHA-256 hash of content:project)          │   │
  │  │ content  │ "Removed Azure Bastion — saves ~$138/month..."          │   │
  │  │ project  │ "oclaw"                                                  │   │
  │  │ tags     │ "type:decision,domain:infrastructure,decided:2026-02-22" │   │
  │  │ active   │ 1                                                        │   │
  │  │ created  │ 2026-02-22 20:15:03                                      │   │
  │  └──────────┴──────────────────────────────────────────────────────────┘   │
  │                                                                            │
  │  WHY: instant writes, zero cost, no network needed, deduplicates,          │
  │       acts as sync queue for Azure, survives Azure outages,                │
  │       can rebuild entire Azure index from here if needed                   │
  │                                                                            │
  │  DOES NOT: understand meaning, do semantic search, create embeddings       │
  │  ONLY: stores text + tags reliably, keyword search (FTS5) as fallback      │
  └──────────────────────────────────┬─────────────────────────────────────────┘
                                     │
                                     │  Sends: plain text + metadata
                                     │  Does NOT send: vectors or embeddings
                                     │
                                     ▼

  ═══════════════════════════════════════════════════════════════════════════════════
  STAGE 3: EMBEDDING                            "Make facts searchable by meaning"
  Concern: Convert text → 3072-dim vectors so similar concepts match
  Runs: Daily 20:35 UTC via cron (memory_bridge.py sync)
  ═══════════════════════════════════════════════════════════════════════════════════

  ┌────────────────────────────────────────────────────────────────────────────┐
  │              Azure AI Search — Smart Search Engine (READ STORE)            │
  │              oclaw-search.search.windows.net (oclaw-rg, $74/mo)           │
  │                                                                            │
  │  Receives: plain text documents from SQLite                                │
  │  Generates: vector embeddings AUTOMATICALLY on ingest                      │
  │                                                                            │
  │  ┌─────────────────────────────────────────────────────────────────────┐   │
  │  │  Azure's Integrated Vectorizer (runs server-side, not on our VM)    │   │
  │  │                                                                     │   │
  │  │  Model: text-embedding-3-large (Azure OpenAI deployment)            │   │
  │  │                                                                     │   │
  │  │  "Removed Azure Bastion — saves ~$138/month..."                     │   │
  │  │       ↓                                                             │   │
  │  │  [0.0234, -0.0891, 0.1247, ..., 0.0567]  (3072 dimensions)        │   │
  │  │                                                                     │   │
  │  │  Now "cost savings" or "infrastructure budget" will FIND this       │   │
  │  │  memory even though those exact words aren't in the text            │   │
  │  └─────────────────────────────────────────────────────────────────────┘   │
  │                                                                            │
  │  Three search methods combined (hybrid):                                   │
  │  1. Vector search  — meaning-based (cosine similarity on embeddings)       │
  │  2. BM25 keyword   — exact word matches                                    │
  │  3. Semantic ranker — re-ranks combined results for best answer            │
  │                                                                            │
  │  WHY: "lunch" finds "team meal at Nobu", "cost" finds "saves $138/mo"     │
  │  DOES NOT: extract facts, understand conversations, store source of truth  │
  │  ONLY: embeds text into vectors + answers "what memories match this?"      │
  └──────────────────────────────────┬─────────────────────────────────────────┘
                                     │
                                     ▼

  ═══════════════════════════════════════════════════════════════════════════════════
  STAGE 4: RECALL                               "Give BarneyBot the right memories"
  Concern: Fast retrieval — pick 3-5 relevant facts for the current conversation
  Runs: Every conversation turn (~0.13s) or on-demand
  ═══════════════════════════════════════════════════════════════════════════════════

                   ┌─────────────────┴──────────────────┐
                   │          RECALL (2 paths)          │
                   │                                    │
         ┌─────────────────────┐          ┌─────────────────────────┐
         │  HOOK (always-on)   │          │  SKILL.md (on-demand)   │
         │                     │          │                         │
         │  before_agent_start │          │  Deep recall for        │
         │  fires every turn   │          │  topic-specific search  │
         │  ~0.13s latency     │          │  richer results         │
         │                     │          │                         │
         │  Returns 3-5 facts  │          └────────────┬────────────┘
         │  as <clawbot_context>│                      │
         └─────────┬───────────┘                       │
                   │                                   │
                   ▼                                   ▼
         ┌───────────────────────────────────────────────────────┐
         │                   BARNEYBOT (ClawBot)                 │
         │                                                       │
         │  Responds with context-aware memory in Telegram/Web   │
         └───────────────────────────────────────────────────────┘

         FALLBACK: Azure AI Search ──▶ SQLite FTS5 (keyword) ──▶ skip


  ═══════════════════════════════════════════════════════════════════════════════════
  SEPARATION OF CONCERNS — EACH STAGE HAS ONE JOB
  ═══════════════════════════════════════════════════════════════════════════════════

  ┌──────────────┬──────────────────────┬────────────────────────────────────────┐
  │ Stage        │ Component            │ One Job                                │
  ├──────────────┼──────────────────────┼────────────────────────────────────────┤
  │ 1. UNDERSTAND│ GPT-5.2 (LLM)       │ Read conversations → extract facts     │
  │              │                      │ Does NOT store or embed anything       │
  ├──────────────┼──────────────────────┼────────────────────────────────────────┤
  │ 2. STORE     │ SQLite (mem.py)      │ Save facts as plain text + tags        │
  │              │                      │ Does NOT understand meaning or embed   │
  ├──────────────┼──────────────────────┼────────────────────────────────────────┤
  │ 3. EMBED     │ Azure AI Search      │ Turn text → 3072-dim vectors           │
  │              │ (text-embedding-     │ Does NOT extract facts or store truth  │
  │              │  3-large)            │                                        │
  ├──────────────┼──────────────────────┼────────────────────────────────────────┤
  │ 4. RECALL    │ Hook / SKILL.md      │ Query Azure → return relevant facts    │
  │              │                      │ Does NOT extract, store, or embed      │
  └──────────────┴──────────────────────┴────────────────────────────────────────┘


  CRON SCHEDULE (UTC):
  ┌──────────┬─────────────────────────┬──────────────────────────┐
  │  20:10   │  session_format_watchdog │  Validate before extract │
  │  20:15   │  smart_extractor sweep   │  Stage 1: UNDERSTAND     │
  │          │                          │  Stage 2: STORE          │
  │  20:35   │  memory_bridge sync      │  Stage 3: EMBED          │
  │  03:00   │  log rotation            │  Keep 7 days             │
  └──────────┴─────────────────────────┴──────────────────────────┘
  Stage 4 (RECALL) runs on every BarneyBot conversation turn, not via cron.
```
