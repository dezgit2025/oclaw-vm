# Azure AI Search & Brain Skill — Phase I Cost Estimates

**Date:** 2026-02-23
**Context:** Cost analysis for the OpenClaw Brain upgrade (memory skill wired into live gateway)

---

## Current Azure AI Search Deployment

| Detail | Value |
|--------|-------|
| Service name | `oclaw-search` |
| Resource group | `oclaw-rg` (NOT `RG_OCLAW2026`) |
| SKU | **Basic** |
| Replicas | 1 |
| Partitions | 1 |
| Semantic ranker | Free tier |
| Location | East US 2 |
| Status | Running |
| Indexes | `clawbot-memory-store`, `clawbot-learning-store` |

**Note:** The search service is in `oclaw-rg`, not `RG_OCLAW2026` where the VM lives. Keep this in mind for Phase 0 pre-flight checks.

---

## Cron Job Frequency

| Job | Frequency | Schedule (UTC) | What It Does |
|-----|-----------|----------------|--------------|
| Extraction sweep | Once/day | `15 20 * * *` (4:15 PM ET) | Reads new session JSONL, sends to GPT-5.2 for fact extraction, stores in SQLite |
| Azure sync | Once/day | `35 20 * * *` (4:35 PM ET / 20:35 UTC) | Embeds new memories (text-embedding-3-large), uploads to Azure AI Search — runs 20 min after extraction |
| Weekly review | Once/week | `0 0 * * 0` (Sunday midnight) | GPT-5.2 analyzes sessions, optimizes SKILL.md files (disabled for v1) |
| Log rotation | Once/day | `0 3 * * *` (3 AM) | Deletes logs older than 7 days |

---

## Monthly Cost Breakdown

### 1. Azure AI Search Hosting (fixed cost)

| Component | Monthly Cost |
|-----------|-------------|
| Basic tier, 1 Search Unit (1 replica x 1 partition) | **~$74** |
| Semantic ranker (free tier) | $0 |
| Per-query charges | **$0** (flat-rate billing, not per-query) |
| **Subtotal** | **~$74** |

Azure AI Search is flat-rate — you pay for the service regardless of query volume. No per-query cost.

### 2. Daily Extraction Cron (GPT-5.2 via Azure OpenAI)

Processes new session content since last run. Estimate ~50K input + ~10K output tokens/day.

| Component | Rate | Daily | Monthly (30d) |
|-----------|------|-------|---------------|
| GPT-5.2 input (~50K tokens/day) | $0.00175/1K tokens | $0.09 | **$2.63** |
| GPT-5.2 output (~10K tokens/day) | $0.014/1K tokens | $0.14 | **$4.20** |
| **Subtotal** | | $0.23 | **$6.83** |

### 3. Hook Injection (per-turn, ~50 turns/day)

Every ClawBot turn: embed user message, query Azure AI Search, prepend 3-5 facts (~200 tokens).

| Component | Rate | Daily | Monthly (30d) |
|-----------|------|-------|---------------|
| Embed queries (text-embedding-3-large, 50x ~100 tokens) | $0.00013/1K tokens | $0.001 | **$0.02** |
| Azure AI Search queries | $0 (flat-rate) | $0 | **$0** |
| **Subtotal** | | $0.001 | **$0.02** |

### 4. Deep Recall via SKILL.md (on-demand, ~5x/day)

Agent-driven topic expansion + hybrid search. GPT-5.2 for topic expansion.

| Component | Rate | Daily | Monthly (30d) |
|-----------|------|-------|---------------|
| GPT-5.2 input (~25K tokens/day) | $0.00175/1K tokens | $0.04 | **$1.31** |
| GPT-5.2 output (~5K tokens/day) | $0.014/1K tokens | $0.07 | **$2.10** |
| **Subtotal** | | $0.11 | **$3.41** |

### 5. Azure Sync (daily embedding of new memories)

~10 new memories/day, ~500 tokens each, embedded via text-embedding-3-large.

| Component | Rate | Daily | Monthly (30d) |
|-----------|------|-------|---------------|
| Embed memories (text-embedding-3-large, ~5K tokens/day) | $0.00013/1K tokens | $0.001 | **$0.02** |

---

## Total Monthly Cost

| Component | Monthly |
|-----------|---------|
| Azure AI Search (basic, 1 SU) | ~$74.00 |
| GPT-5.2 extraction (daily cron) | ~$6.83 |
| GPT-5.2 deep recall (on-demand) | ~$3.41 |
| Embeddings (queries + sync) | ~$0.04 |
| **Total** | **~$84/month** |

### Cost by Category

| Category | Monthly | % of Total |
|----------|---------|------------|
| Infrastructure (AI Search hosting) | ~$74 | 88% |
| Compute (GPT-5.2 tokens) | ~$10 | 12% |
| Embeddings | ~$0.04 | <1% |

---

## Cost Optimization Notes

- **AI Search is 88% of the cost.** If you could use free tier (3 indexes, 50MB, no semantic ranker, no SLA), total drops to ~$10/month. But free tier lacks semantic ranking and has no SLA.
- **GPT-5 mini** ($0.25/$2.00 per 1M tokens) could replace GPT-5.2 for extraction if quality is sufficient — would drop GPT costs from ~$10 to ~$1/month.
- **Batch API** for daily extraction gives 50% discount on GPT costs (async processing is fine for cron jobs).
- **Prompt caching** on GPT-5.2: cached input tokens cost $0.175/1M (90% cheaper). If extraction uses a repeated system prompt, this helps.

---

## Pricing Sources (February 2026)

| Model/Service | Input (per 1K tokens) | Output (per 1K tokens) |
|---------------|----------------------|------------------------|
| GPT-5.2 | $0.00175 | $0.014 |
| GPT-5 | $0.00125 | $0.010 |
| text-embedding-3-large | $0.00013 | N/A |
| Azure AI Search Basic | ~$74/month flat | N/A |

Sources: Azure OpenAI pricing page, Azure AI Search pricing page
