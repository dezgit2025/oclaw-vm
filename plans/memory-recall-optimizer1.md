# Memory Recall Optimizer — Plan v1.1

**Owner:** Des Villa
**Date:** 2026-03-28 (updated with research findings)
**Status:** Ready to implement
**Depends on:** MEMORY-CI-LOOP.PRD (Phase 2: Recall Benchmark)
**Research:** plans/research-log.md (2026-03-28 entries — 3 research sessions, 60+ sources)

---

## Goal

Build an LLM-as-judge recall benchmark, measure retrieval quality, implement improvements, validate locally on MacBook, then deploy to OpenClaw VM. Each round is self-contained: change → benchmark → judge → compare.

---

## What We Have (Local on Mac)

| Asset | Path | Notes |
|-------|------|-------|
| SQLite memory DB | `~/.agent-memory/memory.db` | 384 KB, ~100 active memories, WAL mode |
| Search CLI | `~/.agent-memory/cli/mem.py` | Keyword scoring, <5ms latency |
| Recall code | `~/Projects/oclaw_brain/oclaw_brain_skill_v1/smart_extractor.py` | `cmd_recall()`, topic expansion, priority ranking |
| Hybrid search | `~/Projects/oclaw_brain/oclaw_brain_skill_v1/memory_bridge.py` | Azure hybrid + local fallback |
| Test suite | `~/Projects/oclaw_brain/tests/test_mem_cli.py` | 14 pytest tests with DB isolation fixtures |
| Azure E2E tests | `~/Projects/oclaw_brain/tests/test_azure_e2e.py` | Requires `AZURE_SEARCH_ENDPOINT` env |

---

## Architecture: Local Test → Compare → Push

```
MacBook (local testing)                     OpenClaw VM (production)
┌─────────────────────────────┐             ┌──────────────────────┐
│ Round 1: Baseline + judge    │             │                      │
│ Round 2: RRF fusion + judge  │             │                      │
│ Round 3: Query quality +judge│    scp →    │ Round 6: Deploy      │
│ Round 4: Embed quality +judge│             │   + Azure validate   │
│ Round 5: Full benchmark      │             │                      │
└─────────────────────────────┘             └──────────────────────┘
```

**Why local first:** Zero cost for search queries, instant iteration, full control over test data.

---

## Research-Backed Improvements (Ranked by Impact)

Findings from 3 research sessions (60+ sources including Anthropic, Mem0, Zep/Graphiti, Letta, RAGAS, RAG-Fusion, A-MAC).

| # | Improvement | Impact | Effort | Round | Source |
|---|------------|--------|--------|-------|--------|
| 1 | **RRF fusion** — replace dedup+priority with Reciprocal Rank Fusion | +8-10% accuracy, +30-40% comprehensiveness | 15 lines | Round 2 | RAG-Fusion paper |
| 2 | **Multi-turn context** — pass last 2-3 messages to recall, not just current | +26% F1 (Mem0 LOCOMO benchmark) | 10 lines in hook | Round 3 | Mem0, Zep, Letta consensus |
| 3 | **Dynamic topic expansion + few-shot** — LLM fallback with domain examples | Covers 100% of query domains vs 15 today | 20 lines | Round 3 | Promptagator, planned |
| 4 | **Trivial turn gate** — skip recall for "ok", "thanks", "hello" | -20-35% unnecessary calls, saves latency | 5 lines in hook | Round 3 | A-MAC paper, Two-Room Memory |
| 5 | **Contextual metadata prefix** — prepend project/tags/date before embedding | +5-15% recall (Anthropic: -49% failed retrievals) | 15 lines in bridge | Round 4 | Anthropic Contextual Retrieval |
| 6 | **access_count scoring boost** — logarithmic boost for frequently-recalled | Small but free signal | 5 lines | Round 4 | Planned |

**Not worth it at ~100-fact scale:** ColBERT/late interaction (no Azure support), Voyage-3.5 migration (below noise floor), graph memory (Neo4j overhead), cross-encoder reranking (exceeds 4s budget), full Mem0/Zep adoption (replaces working infra).

**Critical finding — Azure text_weights:** Scoring profile `text_weights` are **silently erased** after Azure semantic reranking. Only scoring functions (freshness, magnitude) survive. Must verify with `az search service show` before Round 4. Our content:1.5x and tags:1.2x weights may already be dead.

---

## LLM-as-Judge Rubric (Used in Every Round)

### Design Principles (G-Eval Framework)

- **One criterion per judge call** — composite rubrics underperform (0.66 vs 0.51 Spearman correlation)
- **Chain-of-thought before score** — judge must emit REASONING before SCORE
- **Temperature=0** — deterministic scoring
- **Judge model:** GPT-4.1-mini for iteration (~$0.005/round), Claude Sonnet 4.6 for final validation
- **Independent judge family** — GPT-5.2 extracts facts, so Claude Sonnet gives unbiased final scores

### 6 Scoring Dimensions

Rounds 1-4 use only **Relevance + Noise** (the two highest-signal dimensions).
Round 5 expands to all 6.

| Dimension | Weight | What it measures | Used in |
|-----------|--------|------------------|---------|
| **Topical Relevance** | 30% | Does the recalled memory answer the query? | Rounds 1-5 |
| **Noise Penalty** | 10% | Are irrelevant memories absent from results? (5=no noise) | Rounds 1-5 |
| **Specificity** | 20% | Precise enough to be useful, not vaguely related? | Round 5 |
| **Temporal Freshness** | 15% | Most recent version returned for time-sensitive queries? | Round 5 |
| **Actionability** | 15% | Could ClawBot act on this memory in conversation? | Round 5 |
| **Completeness** | 10% | All relevant memories returned, not just one? | Round 5 |

### Behavioral Anchors

#### Topical Relevance (30%)
- **1:** None of the recalled memories relate to the query topic
- **3:** At least one memory is relevant, but top-1 is not the best match
- **5:** Top-1 memory directly answers the query; remaining results are topically related

#### Noise Penalty (10%)
- **1:** 3+ irrelevant memories in top 5 results
- **3:** 1-2 irrelevant memories mixed in
- **5:** All recalled memories are relevant (zero noise)

#### Specificity (20%) — Round 5 only
- **1:** Memories are vaguely related (e.g., "something about infrastructure" for a Tailscale query)
- **3:** Memories mention the right topic but lack the specific detail needed
- **5:** Memories contain the exact fact, config value, or decision that answers the query

#### Temporal Freshness (15%) — Round 5 only
- **1:** Returned a superseded memory when a newer version exists
- **3:** Returned both old and new versions (ambiguous which is current)
- **5:** Most recent/authoritative version is top-ranked (or query is not time-sensitive → auto 5)

#### Actionability (15%) — Round 5 only
- **1:** Memory is a bare fact with no context — ClawBot couldn't use it in conversation
- **3:** Memory is useful but requires additional context to act on
- **5:** Memory is self-contained and directly usable in a response

#### Completeness (10%) — Round 5 only
- **1:** Multiple relevant memories exist but only 1 was recalled
- **3:** Most relevant memories recalled, 1-2 missing
- **5:** All relevant memories in the benchmark are present in results

### Judge Prompt Template (Per Dimension)

```
You are evaluating the quality of a memory recall system.

QUERY: "{query}"
CATEGORY: {category}

RECALLED MEMORIES (top 5):
{formatted_memories}

EXPECTED MEMORY IDS: {expected_ids}

---

Score ONLY on this dimension:

## {DIMENSION_NAME}
{dimension_description}

Behavioral anchors:
- 1: {anchor_1_description}
- 3: {anchor_3_description}
- 5: {anchor_5_description}

First, write your REASONING (2-3 sentences analyzing the recall results).
Then output your SCORE as a single integer 1-5.

Format:
REASONING: ...
SCORE: N
```

---

## Round 1: Baseline Measurement [1h]

**Goal:** Get a number. Export memories, build 20 queries, run recall, judge on 2 dimensions.

### Step 1.1: Export Memory Snapshot

Export all active memories to a reproducible JSON fixture.

**File:** `quality/recall/export_snapshot.py`

```bash
python3 quality/recall/export_snapshot.py --db ~/.agent-memory/memory.db \
  --output quality/data/memory_snapshot.json
```

### Step 1.2: Generate 20 Benchmark Queries

Start small — 10 verbatim + 10 temporal. Two highest-value categories.

| Category | Count | Method |
|----------|-------|--------|
| Verbatim fact recall | 10 | GPT-4.1-mini: "What question would this memory answer?" per top-10 memory |
| Temporal ordering | 10 | Manual: "What did we decide about X?" for decisions with dates |

**File:** `quality/data/recall_benchmark.json`

```json
[
  {
    "id": "q001",
    "query": "What model does the gateway use?",
    "category": "verbatim",
    "expected_memory_ids": ["mem_4d8cda41"],
    "expected_keywords": ["claude-opus-4.6", "github-copilot"],
    "expected_absent": false,
    "difficulty": "easy"
  }
]
```

### Step 1.3: Run Baseline Recall

Run all 20 queries through current `cmd_recall()` against local SQLite.

```bash
python3 quality/recall/run_benchmark.py \
  --benchmark quality/data/recall_benchmark.json \
  --db ~/.agent-memory/memory.db \
  --output quality/data/round1-baseline.json
```

### Step 1.4: Judge Baseline (2 dimensions)

Score each query on **Relevance** and **Noise** only (40 judge calls total).

```bash
python3 quality/recall/judge_recall.py \
  --input quality/data/round1-baseline.json \
  --dimensions relevance,noise \
  --model gpt-4.1-mini \
  --output quality/data/round1-scores.json
```

### Step 1.5: Compute Metrics

```
ROUND 1 BASELINE:
  Precision@5:        ???
  MRR:                ???
  Relevance (avg):    ???/5.0
  Noise (avg):        ???/5.0
  Weighted score:     ???/5.0
```

### Round 1 Deliverables
- [ ] `quality/data/memory_snapshot.json` — pinned memory export
- [ ] `quality/data/recall_benchmark.json` — 20 curated queries
- [ ] `quality/data/round1-baseline.json` — recall results
- [ ] `quality/data/round1-scores.json` — judge scores + metrics
- [ ] Baseline numbers documented

### Round 1 Cost: ~$0.02 (20 queries x 2 dimensions x GPT-4.1-mini)

---

## Round 2: RRF Fusion [1h]

**Goal:** Replace dedup+priority sort with Reciprocal Rank Fusion. This is the highest-ROI single code change identified by research (+8-10% accuracy, +30-40% comprehensiveness).

### Why RRF

Current approach: run 5 expanded queries, collect results, deduplicate by ID, sort by tag-type priority. This throws away ranking signal — a memory appearing in 4 of 5 query results ranks the same as one appearing in 1.

RRF rewards consensus: memories retrieved by multiple sub-queries get a boosted fused score. The formula:

```
RRF_score(memory) = SUM over all queries [ 1 / (k + rank_in_query) ]
```

Where `k` is a constant (typically 10-60; research says k=10 is better for small stores with few queries).

### Step 2.1: Implement RRF in `cmd_recall()`

**File:** `smart_extractor.py` → `cmd_recall()`

Replace the current dedup+priority sort block with:

```python
def rrf_fuse(query_results: list[list[dict]], k: int = 10) -> list[dict]:
    """Reciprocal Rank Fusion across multiple query result lists."""
    scores = {}  # memory_id → cumulative RRF score
    memory_map = {}  # memory_id → memory dict

    for results in query_results:
        for rank, mem in enumerate(results):
            mid = mem["id"]
            memory_map[mid] = mem
            scores[mid] = scores.get(mid, 0) + 1.0 / (k + rank + 1)

    # Sort by RRF score descending, then by tag priority as tiebreaker
    ranked = sorted(
        scores.keys(),
        key=lambda mid: (
            -scores[mid],
            -memory_map[mid].get("priority", 0),
        ),
    )
    return [memory_map[mid] for mid in ranked]
```

**Change in `cmd_recall()`:**
```python
# Before: flat list + dedup + priority sort
# After:
all_query_results = []
for q in search_queries:
    results = run_search(q, k=5)
    all_query_results.append(results)

memories = rrf_fuse(all_query_results, k=10)[:max_memories]
```

### Step 2.2: Re-run Benchmark + Judge

```bash
python3 quality/recall/run_benchmark.py \
  --benchmark quality/data/recall_benchmark.json \
  --db ~/.agent-memory/memory.db \
  --output quality/data/round2-results.json

python3 quality/recall/judge_recall.py \
  --input quality/data/round2-results.json \
  --dimensions relevance,noise \
  --model gpt-4.1-mini \
  --output quality/data/round2-scores.json
```

### Step 2.3: Compare Round 1 → Round 2

```bash
python3 quality/recall/regression_gate.py \
  --before quality/data/round1-scores.json \
  --after quality/data/round2-scores.json
```

### Round 2 Deliverables
- [ ] `smart_extractor.py` updated with `rrf_fuse()` function
- [ ] `quality/data/round2-scores.json` — judge scores
- [ ] Before/after comparison documented
- [ ] Expected: +8-10% on Precision@5

### Round 2 Cost: ~$0.02 (judge only)

---

## Round 3: Query Quality Bundle [1.5h]

**Goal:** Three improvements to how the query reaches search — better expansion, more context, fewer wasted calls. All modify the query side, not the index side.

### Step 3.1: Dynamic Topic Expansion + Few-Shot Examples

**Problem:** Static 15-domain map. Queries outside these domains get no expansion.

**Fix:** LLM fallback with 3-5 domain-specific few-shot examples (Promptagator technique).

**File:** `smart_extractor.py` → `_expand_topic_queries()`

```python
FEW_SHOT_EXAMPLES = """
Examples of good expansions for this domain:
- "tailscale" → tailscale, VPN, wireguard, exit node, mesh network
- "gateway model" → gateway, claude-opus, copilot, LLM, model config
- "reauth" → reauth, OAuth, token refresh, google auth, credentials
- "memory extraction" → extraction, smart_extractor, session facts, GPT-5.2
- "azure cost" → azure cost, billing, cost management, foundry spend
"""

def _expand_topic_queries(topic: str) -> list[str]:
    queries = [topic]

    # Try static map first (free, instant)
    for key, expansions in DOMAIN_MAP.items():
        if key in topic.lower():
            queries.extend(expansions)
            break

    # If no static match, use LLM with few-shot examples (~200ms, ~$0.001)
    if len(queries) == 1:
        prompt = f"""{FEW_SHOT_EXAMPLES}
Now expand: "{topic}" → Return comma-separated list of 3-5 search terms only."""
        expansions = call_llm(prompt, model="gpt-4.1-mini", temperature=0)
        queries.extend([e.strip() for e in expansions.split(",")])

    return list(dict.fromkeys(queries))[:8]
```

### Step 3.2: Multi-Turn Retrieval Context

**Problem:** Hook passes only the last user message. Intent is often distributed across turns.

**Research:** All production systems (Mem0, Zep, Letta) use 2-4 previous turns. Mem0 reports +26% F1 on LOCOMO benchmark.

**Fix:** Pass last 2-3 messages to recall, not just the current one.

**File:** `handler.js` (hook)

```javascript
// Before: only last user message
const lastUser = [...messages].reverse().find((m) => m.role === "user");

// After: last 3 messages (any role) for context, last user for primary query
const recentMessages = messages.slice(-3);
const context = recentMessages
  .map((m) => {
    const text = typeof m.content === "string" ? m.content :
      m.content.filter(b => b.type === "text").map(b => b.text).join(" ");
    return text;
  })
  .join(" | ");
const truncated = context.substring(0, 300);  // Slightly larger window
```

### Step 3.3: Trivial Turn Gate

**Problem:** "ok", "thanks", "hello" trigger full Azure recall for no value. Wastes ~130ms + API cost.

**Research:** A-MAC paper (ICLR 2026) shows triviality is a tight semantic cluster. Simple heuristic catches 95%+ of cases.

**Fix:** Skip recall if message is short and contains no proper nouns or domain terms.

**File:** `handler.js` (hook)

```javascript
// Trivial turn gate — skip recall for ack messages
const TRIVIAL_PATTERNS = /^(ok|okay|sure|thanks|thank you|got it|yes|no|yep|nope|cool|nice|hello|hi|hey)\b/i;
if (query.length < 25 && TRIVIAL_PATTERNS.test(query.trim())) {
  return {};  // No context injection
}
```

### Step 3.4: Re-run Benchmark + Judge

```bash
python3 quality/recall/run_benchmark.py \
  --benchmark quality/data/recall_benchmark.json \
  --db ~/.agent-memory/memory.db \
  --output quality/data/round3-results.json

python3 quality/recall/judge_recall.py \
  --input quality/data/round3-results.json \
  --dimensions relevance,noise \
  --model gpt-4.1-mini \
  --output quality/data/round3-scores.json

python3 quality/recall/regression_gate.py \
  --before quality/data/round2-scores.json \
  --after quality/data/round3-scores.json
```

### Round 3 Deliverables
- [ ] `smart_extractor.py` updated with few-shot expansion
- [ ] `handler.js` updated with multi-turn context + trivial gate
- [ ] `quality/data/round3-scores.json` — judge scores
- [ ] Before/after comparison documented
- [ ] Expected: topic expansion covers 100% of queries; multi-turn boosts temporal queries

### Round 3 Cost: ~$0.04 (judge + LLM expansion for ~20 queries)

---

## Round 4: Embedding & Scoring Quality [1h]

**Goal:** Improve the index side — better embeddings and better scoring. Requires Azure re-index.

### Step 4.1: Contextual Metadata Prefix on Embeddings

**Research:** Anthropic's Contextual Retrieval reduces failed retrievals by 49%. For our ~100-fact store, a zero-cost metadata prefix gives 5-15% improvement without LLM calls.

**Problem:** A fact like "Port 18793 is used for this service" has ambiguous embedding without project/domain context.

**Fix:** Prepend metadata before embedding in `memory_bridge.py`.

**File:** `memory_bridge.py` → document preparation for Azure sync

```python
def prepare_embed_content(fact: dict) -> str:
    """Prepend metadata context to fact before embedding.
    Improves vector similarity for project-scoped and tagged queries."""
    prefix_parts = []
    if fact.get("project"):
        prefix_parts.append(f"Project: {fact['project']}")
    if fact.get("tags"):
        prefix_parts.append(f"Tags: {fact['tags']}")
    if fact.get("created_at"):
        prefix_parts.append(f"Date: {fact['created_at'][:10]}")
    prefix = " | ".join(prefix_parts)
    return f"[{prefix}]\n{fact['content']}" if prefix else fact["content"]
```

**Note:** The `content` field displayed in recall results stays unchanged — only the embedding input is augmented. Requires `memory_bridge.py sync --full` to re-embed all memories.

### Step 4.2: access_count Scoring Boost

**File:** `memory_bridge.py` → `ensure_memory_index()` scoring profile

```python
# Add to scoring_profile.functions list:
MagnitudeScoringFunction(
    field_name="access_count",
    boost=1.3,
    interpolation="logarithmic",  # Diminishing returns
    parameters=MagnitudeScoringParameters(
        boosting_range_start=0,
        boosting_range_end=20,
    ),
),
```

### Step 4.3: Verify Azure text_weights Behavior

**Critical finding:** Azure `text_weights` in scoring profiles may be **silently erased** after semantic reranking. Only scoring functions (freshness, magnitude) survive.

```bash
az search service show --name oclaw-search --resource-group oclaw-rg \
  --query "semanticSearch" -o tsv
```

If confirmed, remove `text_weights` from our scoring profile definition — they're dead code. The semantic ranker handles content vs tags weighting internally.

### Step 4.4: Re-run Benchmark + Judge

Round 4 changes affect Azure, not local SQLite. Local benchmark measures the contextual prefix impact on `mem.py search` keyword matching (metadata terms become searchable). Full Azure validation happens in Round 6.

```bash
python3 quality/recall/run_benchmark.py \
  --benchmark quality/data/recall_benchmark.json \
  --db ~/.agent-memory/memory.db \
  --output quality/data/round4-results.json

python3 quality/recall/judge_recall.py \
  --input quality/data/round4-results.json \
  --dimensions relevance,noise \
  --model gpt-4.1-mini \
  --output quality/data/round4-scores.json

python3 quality/recall/regression_gate.py \
  --before quality/data/round3-scores.json \
  --after quality/data/round4-scores.json
```

### Round 4 Deliverables
- [ ] `memory_bridge.py` updated with contextual prefix + access_count boost
- [ ] Azure text_weights behavior verified
- [ ] `quality/data/round4-scores.json` — judge scores
- [ ] Before/after comparison documented
- [ ] Decision: text_weights kept or removed?

### Round 4 Cost: ~$0.02 (judge only)

### Stop Gate After Round 4

```
IF weighted_score >= 3.5 AND precision@5 >= 0.60:
    → Skip to Round 6 (deploy)
ELSE:
    → Continue to Round 5 (expand benchmark for deeper diagnosis)
```

---

## Round 5: Full Benchmark Expansion [2h]

**Goal:** Expand to 80 queries + all 6 judge dimensions for comprehensive evaluation. Only if Rounds 1-4 didn't meet targets, OR as pre-deploy validation.

### Step 5.1: Expand to 80 Queries

| Category | Count | What it tests |
|----------|-------|---------------|
| Verbatim fact recall | 16 | Direct factual retrieval |
| Temporal ordering | 16 | "What did we decide AFTER X?" |
| Knowledge update | 12 | Superseded facts (should return latest) |
| Multi-hop synthesis | 12 | Requires combining 2+ memories |
| Hard negatives | 12 | Similar topic but wrong answer |
| Abstention | 12 | No relevant memory exists — should return nothing |

### Step 5.2: Judge on All 6 Dimensions (480 calls)

```bash
python3 quality/recall/judge_recall.py \
  --input quality/data/round5-results.json \
  --dimensions relevance,noise,specificity,freshness,actionability,completeness \
  --model gpt-4.1-mini \
  --output quality/data/round5-scores.json
```

### Step 5.3: Final Validation with Claude Sonnet (480 calls)

Unbiased cross-family judge for final assessment.

```bash
python3 quality/recall/judge_recall.py \
  --input quality/data/round5-results.json \
  --dimensions relevance,noise,specificity,freshness,actionability,completeness \
  --model claude-sonnet-4-6 \
  --output quality/data/round5-scores-sonnet.json
```

### Step 5.4: Diagnostic Report by Category + Dimension

```
ROUND 5 FULL BENCHMARK:
  Overall weighted:    ???/5.0

  By category:
    Verbatim:          ???/5.0
    Temporal:          ???/5.0
    Knowledge update:  ???/5.0
    Multi-hop:         ???/5.0
    Hard negatives:    ???/5.0
    Abstention:        ???/5.0

  By dimension:
    Relevance:         ???/5.0
    Noise:             ???/5.0
    Specificity:       ???/5.0
    Freshness:         ???/5.0
    Actionability:     ???/5.0
    Completeness:      ???/5.0
```

### Round 5 Cost: ~$0.15 (GPT-4.1-mini) + ~$2.40 (Claude Sonnet) = ~$2.55

---

## Round 6: Deploy to OpenClaw VM [30m]

**Goal:** Ship validated improvements to production. Run Azure benchmark as final check.

### Step 6.1: Deploy Changed Files

```bash
scp smart_extractor.py oclaw:~/.openclaw/workspace/skills/clawbot-memory/
scp memory_bridge.py oclaw:~/.openclaw/workspace/skills/clawbot-memory/

# Deploy hook changes
scp handler.js oclaw:~/.openclaw/hooks/clawbot-memory/

# Deploy benchmark tools
scp -r quality/ oclaw:~/.openclaw/workspace/skills/clawbot-memory/quality/
```

### Step 6.2: Re-index Azure (Contextual Prefix + Scoring Profile)

```bash
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory && \
  source .venv/bin/activate && \
  python3 memory_bridge.py sync --full"
```

### Step 6.3: Run Azure Benchmark on VM

```bash
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory && \
  source .venv/bin/activate && \
  python3 quality/recall/run_benchmark.py --backend azure \
    --benchmark quality/data/recall_benchmark.json \
    --output /tmp/vm-azure-results.json"
```

### Step 6.4: Compare Local vs Azure

```bash
scp oclaw:/tmp/vm-azure-results.json quality/data/round6-azure-results.json

python3 quality/recall/compare_backends.py \
  --local quality/data/round4-results.json \
  --azure quality/data/round6-azure-results.json
```

**Expected:** Azure scores higher (hybrid search + semantic reranking > keyword-only).

### Step 6.5: Restart Gateway + Smoke Test

```bash
ssh oclaw "python3 /home/desazure/.openclaw/workspace/ops/watchdog/restart_gateway.py"
```

Send a test message through ClawBot and verify `<clawbot_context>` appears with relevant memories.

### Round 6 Cost: $0.00 (Azure Search included in $74/mo)

---

## Round 7: LLM Topic Expansion [30m]

**Goal:** Replace the dumb word-based fallback in `_expand_topic_queries()` with GPT-4.1-mini LLM expansion + in-memory cache. Directly improves the #3 ranked improvement (topic expansion) which feeds RRF fusion (#1 ranked). Low effort, high compounding ROI.

**Research:** The word-based fallback generates bigrams which are low-quality expansions. GPT-4.1-mini can generate semantically meaningful related terms for any domain, even ones not in the static map.

### Step 7.1: Implement LLM Expansion + Cache

**File:** `smart_extractor.py` → `_expand_topic_queries()` + new `_llm_expand_query()`

```python
_LLM_EXPANSION_CACHE: dict[str, list[str]] = {}

def _llm_expand_query(query: str) -> list[str]:
    """Call GPT-4.1-mini to generate 5 related search terms. 1s timeout."""
    from openai import OpenAI
    client = OpenAI(base_url="http://127.0.0.1:18791/v1", api_key="LOCAL")
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{
            "role": "user",
            "content": f"Given this search query, generate 5 related search terms "
                       f"that would find relevant memories. Return only the terms, "
                       f"one per line.\n\nQuery: {query}"
        }],
        temperature=0.0,
        timeout=1.0,
    )
    return [line.strip() for line in resp.choices[0].message.content.strip().split("\n") if line.strip()]
```

**Integration into `_expand_topic_queries()`:**
```
1. Try static domain map         → ~0ms (covers ~70% of queries)
2. Check _LLM_EXPANSION_CACHE   → ~0ms
3. Call _llm_expand_query()      → ~200-400ms, GPT-4.1-mini
4. Cache result in dict
5. Fall back to word-based on any failure (timeout, proxy down, etc.)
6. Cap at 8 unique queries       → existing dedup + slice
```

### Step 7.2: Test on VM with Novel Queries

Test 5 novel queries with no static map match:
- "kubernetes pod scheduling"
- "terraform state management"
- "webhook retry logic"
- "rate limiting strategy"
- "backup rotation policy"

Verify: LLM returns meaningful terms, cache hits return instantly, timeout falls back to bigrams.

### Step 7.3: Re-run Benchmark + Judge + Compare

```bash
python3 quality/recall/run_benchmark.py \
  --benchmark quality/data/recall_benchmark.json \
  --db ~/.agent-memory/memory.db \
  --output quality/data/round7-results.json \
  --mode rrf

python3 quality/recall/judge_recall.py \
  --input quality/data/round7-results.json \
  --dimensions relevance,noise \
  --output quality/data/round7-scores.json

python3 quality/recall/regression_gate.py \
  --before quality/data/round4-scores.json \
  --after quality/data/round7-scores.json
```

### Step 7.4: Deploy to VM + Restart Gateway

```bash
scp smart_extractor.py oclaw:~/.openclaw/workspace/skills/clawbot-memory/
ssh oclaw "python3 /home/desazure/.openclaw/workspace/ops/watchdog/restart_gateway.py"
```

### Round 7 Deliverables
- [ ] `_llm_expand_query()` function in `smart_extractor.py`
- [ ] In-memory cache for LLM expansions
- [ ] Timeout fallback to word-based expansion
- [ ] `quality/data/round7-scores.json` — judge scores
- [ ] Before/after comparison documented
- [ ] Expected: improved recall on novel/cross-domain queries

### Round 7 Cost: ~$0.001 per cache miss (~$0.01/month at current volume)

---

## Regression Gate (Used After Every Round)

**File:** `quality/recall/regression_gate.py`

```python
MINIMUM_THRESHOLDS = {
    "precision_at_5": 0.60,
    "mrr": 0.70,
    "weighted_judge_score": 3.5,
}

def check_regression(before: dict, after: dict) -> dict:
    """Compare before/after. Returns pass/fail + deltas."""
    results = {}
    for metric, threshold in MINIMUM_THRESHOLDS.items():
        delta = after[metric] - before[metric]
        passed = after[metric] >= threshold and delta >= -0.05
        results[metric] = {
            "before": before[metric],
            "after": after[metric],
            "delta": delta,
            "threshold": threshold,
            "passed": passed,
        }
    return {
        "all_passed": all(r["passed"] for r in results.values()),
        "metrics": results,
    }
```

---

## File Structure (New Files)

```
quality/
  __init__.py
  recall/
    __init__.py
    export_snapshot.py          # Export memories to JSON fixture
    generate_queries.py         # Mine + synthesize benchmark queries
    run_benchmark.py            # Execute queries against local or Azure
    judge_recall.py             # LLM-as-judge scoring (configurable dimensions)
    regression_gate.py          # Before/after comparison with thresholds
    compare_backends.py         # Local vs Azure result diff
  data/
    memory_snapshot.json        # Exported memories (pinned snapshot)
    recall_benchmark.json       # 20 queries (Rounds 1-4)
    recall_benchmark_full.json  # 80 queries (Round 5)
    round1-scores.json          # Baseline
    round2-scores.json          # After RRF
    round3-scores.json          # After query quality bundle
    round4-scores.json          # After embed/scoring quality
    round5-scores.json          # Full benchmark (6 dim, GPT-4.1-mini)
    round5-scores-sonnet.json   # Full benchmark (6 dim, Claude Sonnet)
```

9 Python files + 10 data files. Each Python file under 80 lines.

---

## Metrics & Success Criteria

| Metric | Baseline (est.) | Round 4 target | Round 5 target | Measured by |
|--------|-----------------|----------------|----------------|-------------|
| Precision@5 | ~0.40 | >= 0.55 | >= 0.60 | Benchmark |
| MRR | ~0.50 | >= 0.60 | >= 0.70 | Benchmark |
| Relevance (avg) | ~2.5/5.0 | >= 3.2 | >= 3.5 | LLM judge |
| Noise (avg) | ~3.0/5.0 | >= 3.5 | >= 4.0 | LLM judge |
| Weighted score | ~2.5/5.0 | >= 3.2 | >= 3.5 | LLM judge (weighted) |

---

## Cost Summary

| Round | What | Judge calls | Est. cost |
|-------|------|-----------|-----------|
| Round 1 (baseline) | 20q x 2 dim | 40 | ~$0.02 |
| Round 2 (RRF fusion) | 20q x 2 dim | 40 | ~$0.02 |
| Round 3 (query quality) | 20q x 2 dim + LLM expansion | 40 | ~$0.04 |
| Round 4 (embed/scoring) | 20q x 2 dim | 40 | ~$0.02 |
| Round 5 (full benchmark) | 80q x 6 dim x 2 models | 960 | ~$2.55 |
| Round 6 (deploy) | Azure benchmark only | 0 | $0.00 |
| Round 7 (LLM expansion) | 20q x 2 dim + LLM expansion calls | 40 | ~$0.03 |
| **Total** | | **1,160** | **~$2.68** |
| **Ongoing (topic expansion)** | LLM fallback on cache miss | — | **~$0.01/month** |

---

## Execution Summary

```
Round 1: Baseline             20q x 2 dim → get a number                        [1h]
                              Judge: GPT-4.1-mini, 40 calls
                              Output: baseline Precision@5, MRR, weighted score

Round 2: RRF Fusion           Replace dedup+priority → re-run → judge → compare [1h]
                              Judge: GPT-4.1-mini, 40 calls
                              Output: delta vs Round 1 (expected +8-10%)

Round 3: Query Quality        Topic expansion + multi-turn + trivial gate        [1.5h]
                              → re-run → judge → compare
                              Judge: GPT-4.1-mini, 40 calls
                              Output: delta vs Round 2

Round 4: Embed/Scoring        Contextual prefix + access_count + text_weights    [1h]
                              → re-run → judge → compare
                              Judge: GPT-4.1-mini, 40 calls
                              STOP GATE: if targets met → skip to Round 6

Round 5: Full Benchmark       80q x 6 dim (only if needed or pre-deploy)        [2h]
    (only if needed)          Judge: GPT-4.1-mini (480) + Claude Sonnet (480)
                              Output: diagnostic by category + dimension

Round 6: Deploy to VM         scp → re-index → restart → smoke test             [30m]
                              Azure benchmark as final validation

Round 7: LLM Expansion        GPT-4.1-mini fallback for novel queries            [30m]
                              + in-memory cache + timeout fallback
                              Judge: rule-based, 40 calls
                              Output: delta vs Round 4
```

---

## Key Design Decisions

| Decision | Rationale | Source |
|----------|-----------|--------|
| RRF fusion (k=10) before other improvements | Highest ROI single change: +8-10% accuracy, 15 lines, zero API cost | RAG-Fusion paper |
| Multi-turn context (last 3 messages) | All production systems agree: 2-4 turns > last message only. +26% F1. | Mem0, Zep, Letta consensus |
| Trivial gate (regex heuristic) | A-MAC paper: triviality is a tight cluster. 5-line regex catches 95%. | A-MAC (ICLR 2026) |
| Metadata prefix (not full Contextual Retrieval) | Full LLM-generated context is overkill for ~100 atomic facts. Metadata prefix is free and gives 5-15%. | Anthropic blog, adapted |
| Few-shot expansion examples | Promptagator: domain-specific examples dramatically improve expansion for specialized vocab. | Promptagator paper |
| Logarithmic access_count boost | Prevents runaway feedback. First 5 accesses matter most. | Planned |
| GPT-4.1-mini for iteration, Claude Sonnet for final | Same-family bias acceptable for iteration. Cross-family for unbiased final. | G-Eval, LLM-as-judge research |
| 2 dimensions early, 6 dimensions late | Signal-to-noise: Relevance + Noise catch 80% of issues. Full rubric for diagnosis only. | G-Eval framework |
| Stop gate after Round 4 | If targets met, skip $2.55 full benchmark. Deploy wins. | Incremental design |
| Defer Voyage-3.5 migration | Below noise floor for ~100 facts until RRF + contextual prefix are implemented. | Research finding |

---

## Open Questions

1. **Azure text_weights:** Are they already dead code? Must verify before Round 4.
2. **Multi-turn window size:** 2 vs 3 vs 4 previous messages? Start with 3, tune based on benchmark.
3. **Trivial gate false positives:** Will "ok deploy" or "yes that model" get gated? May need entity check.
4. **Contextual prefix re-index cost:** Does `sync --full` trigger re-embedding of all 100 memories? What's the Azure OpenAI embedding cost? (~$0.01 estimated)
5. **ProMem iterative extraction (73.8% vs 41% one-shot)** — worth exploring for multi-hop queries? Deferred.

---

## References

- [RAG-Fusion (arXiv 2402.03367)](https://arxiv.org/abs/2402.03367) — RRF for multi-query retrieval
- [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) — Metadata prefix technique
- [Anthropic — Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Mem0 LOCOMO Benchmark](https://mem0.ai/research) — Multi-turn retrieval +26% F1
- [A-MAC (arXiv 2603.04549)](https://arxiv.org/abs/2603.04549) — Adaptive Memory Admission Control
- [Two-Room Memory Architecture](https://github.com/zachseven/two-room-memory) — Triviality gating
- [Zep Temporal KG (arXiv 2501.13956)](https://arxiv.org/abs/2501.13956) — Temporal edge invalidation
- [Promptagator (arXiv 2209.11755)](https://arxiv.org/abs/2209.11755) — Few-shot query expansion
- [G-Eval Framework](https://www.confident-ai.com/blog/g-eval-the-definitive-guide) — LLM-as-judge rubric
- [Azure Hybrid Search RRF](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)
- [Azure Scoring Profiles + Semantic Ranking](https://learn.microsoft.com/en-us/azure/search/semantic-how-to-enable-scoring-profiles)
- [RAGAS Metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- [Pairwise vs Pointwise Scoring (arXiv 2504.14716)](https://arxiv.org/abs/2504.14716)
- [LongMemEval (ICLR 2025, arXiv 2410.10813)](https://arxiv.org/abs/2410.10813)
- MEMORY-CI-LOOP.PRD (parent document)
- plans/mem-optimize-v5.md (Phase 2 + 3 specs)
- plans/research-log.md (2026-03-28 — full research notes)
