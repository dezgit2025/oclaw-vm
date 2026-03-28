# Memory Optimization Plan v5

**Status:** Draft
**Supersedes:** mem-optimize-v4.md
**Date:** 2026-03-06
**Source research:** plans/mem-best-practice.md

---

## Changes from v4

1. Phase 0 (tag definition injection) extracted to standalone plan — `plans/phase00-tag-definition-injection.md`
2. Added success criteria with measurable targets
3. Split cadence: monthly (cheap automated) vs quarterly (heavier semi-manual)
4. Killed Phase 7b (tag-boosted search) — use scoring profile text_weights instead
5. Added semantic dedup sweep (quarterly)
6. Reordered phases by ROI
7. Kept 21-file structure as-is
8. Added staging index requirement for scoring profile changes

---

## Success Criteria

These define "good enough" — stop tuning when met.

| Metric | Target | Measured By |
|--------|--------|-------------|
| Extraction accuracy | >= 4.0/5 | GPT-4.1-mini scoring (monthly) |
| Atomicity | >= 4.0/5 | GPT-4.1-mini scoring (monthly) |
| Tag anchor coverage | >= 80% have both `type:` and `domain:` | SQLite query (monthly) |
| Tag diversity | No single tag > 25% of total | SQLite query (monthly) |
| Recall Precision@5 | >= 0.6 | Benchmark queries (monthly) |
| Recall MRR | >= 0.7 | Benchmark queries (monthly) |
| Semantic duplicates | < 5% of active memories | LLM dedup sweep (quarterly) |

---

## Cadence

### Monthly (automated cron, ~$0.01/run)

| Component | Method | Cost |
|-----------|--------|------|
| Extraction quality scoring | GPT-4.1-mini scores 30 random memories | $0.005 |
| Failure mode analysis | GPT-4.1-mini classifies rejections | $0.003 |
| Tag analysis | Pure Python — distribution, anchor coverage, drift | $0.00 |
| Recall benchmark | Azure Search queries against test set | $0.00 |
| Report generation | GPT-4.1-mini recommendations | $0.002 |
| **Total** | | **~$0.01** |

### Quarterly (semi-manual, ~$1.50/run)

| Component | Method | Cost |
|-----------|--------|------|
| A/B extraction comparison | GPT-5.2, 8 sessions x2 prompts | $1.40 |
| Semantic dedup sweep | GPT-4.1-mini merges near-duplicates | ~$0.05 |
| TAG_REGISTRY promotion | Review free-form tags with 5+ uses | $0.00 |
| Recall benchmark refresh | Update/add test queries if MRR plateaus | $0.00 |
| **Total** | | **~$1.50** |

### On-Demand (triggered by drift)

| Trigger | Action |
|---------|--------|
| MRR drops below 0.7 | Retune scoring profile weights |
| Stale memories pollute recall | Adjust confidence decay parameters |
| New candidate extraction prompt | Run A/B comparison off-cycle |

---

## Phase Order (by ROI)

| Phase | What | Effort | Prereqs |
|-------|------|--------|---------|
| 0 | Tag definition injection | 30 min | None — separate plan |
| 1 | Tag analysis (zero cost) | 1.5h | None |
| 2 | Recall benchmark (establish baseline) | 2h | None |
| 3 | Scoring profile + recall tuning | 2h | Phase 2 (need baseline) |
| 4 | Extraction quality scoring | 2h | None |
| 5 | Semantic dedup sweep | 1.5h | None |
| 6 | A/B comparison framework | 2h | Phase 4 |
| 7 | Monthly report + cron | 1.5h | Phases 1-4 |
| 8 | Core infrastructure | 1h | First (but build incrementally) |

**Phase 8 (infrastructure)** is listed last because `config.py`, `types.py`, and CLI skeleton should be built incrementally as each phase needs them — not upfront.

---

## Phase 0: Tag Definition Injection

**See:** `plans/phase00-tag-definition-injection.md` (standalone, ready to implement)

---

## Phase 1: Tag Analysis (Zero LLM Cost)

All pure Python against SQLite. Reveals current tag quality before any changes.

### Files

```
quality/tags/
  __init__.py
  analyze_distribution.py     # Tag frequency from SQLite
  check_anchor_coverage.py    # % with type: and domain: present
  find_promotion_candidates.py # Free-form tags with 5+ uses
  detect_tag_drift.py         # Word overlap to find near-duplicate tags
```

### What it measures

| Analysis | Method | Output |
|----------|--------|--------|
| Distribution | `SELECT tags, COUNT(*) FROM memories WHERE active=1 GROUP BY tags` | Top 20 tags + percentages |
| Anchor coverage | Parse tags for `type:` and `domain:` presence | % with type, % with domain, % with both |
| Promotion candidates | Compare TAG_REGISTRY.md to actual usage | Free-form tags used 5+ times |
| Drift detection | Word overlap >50% between tags in same dimension | Near-duplicate pairs to merge |

### CLI

```bash
python3 quality/quality_analyzer.py tags
```

---

## Phase 2: Recall Benchmark (Establish Baseline)

Must come before any recall tuning to measure impact.

### Files

```
quality/recall/
  __init__.py
  build_benchmark.py     # Create/load benchmark queries + expected memory IDs
  run_benchmark.py       # Execute queries against Azure AI Search
  compute_metrics.py     # Precision@k, Recall@k, MRR
quality/data/
  recall_benchmark.json  # Curated test queries (15-20)
```

### Benchmark format

```json
[
  {
    "query": "What model does the gateway use?",
    "expected_memory_ids": ["mem_4d8cda41"],
    "expected_keywords": ["claude-opus-4.6", "github-copilot"],
    "category": "tech_stack"
  }
]
```

### Bootstrap

`build_benchmark.py init` asks GPT-4.1-mini "What question would this memory answer?" for top memories. Human reviews and curates down to 15-20 diverse queries.

### Metrics

- **Precision@5:** Of top 5 returned, how many are relevant?
- **Recall@5:** Of all relevant memories, how many appear in top 5?
- **MRR:** Reciprocal rank of first relevant result

### CLI

```bash
python3 quality/quality_analyzer.py benchmark
```

---

## Phase 3: Scoring Profile + Recall Tuning

Two changes to `memory_bridge.py`. **Requires Phase 2 baseline to measure impact.**

### 3a. Azure Scoring Profile

**IMPORTANT:** Test on staging index first. Production index change may require recreation + full re-sync.

**Step 1:** Create staging index
```bash
# Clone index schema to clawbot-memory-store-staging
# Run memory_bridge.py sync --full against staging
```

**Step 2:** Add scoring profile to index definition

**File:** `/Users/dez/Projects/oclaw_brain/update1/memory_bridge.py` (~line 550)

```python
ScoringProfile(
    name="memory-relevance",
    text_weights=TextWeights(weights={"content": 1.5, "tags": 1.2}),
    functions=[
        ScoringFunction(
            field_name="importance",
            boost=2.0,
            interpolation="linear",
            magnitude=MagnitudeFunction(
                boosting_range_start=1,
                boosting_range_end=10,
            ),
        ),
        ScoringFunction(
            field_name="updated_at",
            boost=1.5,
            interpolation="linear",
            freshness=FreshnessFunction(boosting_duration="P30D"),
        ),
    ],
)
```

Set `scoring_profile="memory-relevance"` in the search call.

**Note:** `tags` field gets weight 1.2 — this replaces the killed Phase 7b (tag-boosted search). The scoring profile handles tag boosting natively without hardcoded keyword mappings.

**Step 3:** Run recall benchmark against staging, compare to baseline

**Step 4:** If improved, promote to production. Run `memory_bridge.py sync --full`.

### 3b. Category from Tags

**File:** `/Users/dez/Projects/oclaw_brain/update1/memory_bridge.py` — `categorize_memory()` (~line 287)

Replace keyword heuristics with tag-derived category:

```python
def categorize_memory(content: str, tags: str = "") -> str:
    if tags:
        if "type:decision" in tags or "type:pivot" in tags:
            return "decision"
        if "type:preference" in tags:
            return "preference"
        if "type:tech_stack" in tags:
            return "tech_stack"
        if "type:architecture" in tags:
            return "architecture"
        if "type:error_pattern" in tags:
            return "error_pattern"
        if "type:context" in tags:
            return "context"
    # Fallback for memories without tags
    if any(w in content.lower() for w in ["chose", "decided"]):
        return "decision"
    if any(w in content.lower() for w in ["prefers", "likes"]):
        return "preference"
    return "general"
```

Update call site to pass tags:
```python
"category": categorize_memory(mem["content"], mem.get("tags", "")),
```

After deploy, run `memory_bridge.py sync --full` to re-categorize all memories.

### Testing

```bash
# Before
python3 quality/quality_analyzer.py benchmark > /tmp/recall-before.json

# Deploy to staging, test
python3 quality/quality_analyzer.py benchmark --index staging > /tmp/recall-staging.json

# Compare
diff /tmp/recall-before.json /tmp/recall-staging.json
```

---

## Phase 4: Extraction Quality Scoring

### Files

```
quality/extraction/
  __init__.py
  sample_memories.py        # Pull N random memories from SQLite
  score_memory.py           # GPT-4.1-mini scores on 4 dimensions
  analyze_pass_rates.py     # Parse extract_state.json for trends
  identify_failure_modes.py # Classify rejections by type
```

### Scoring prompt (per memory)

```
Score this extracted memory on 4 dimensions (1-5):

MEMORY: "{content}"
TAGS: [{tags}]
PROJECT: {project}

1. ACCURACY -- Real verifiable fact, not hallucination or opinion?
2. ATOMICITY -- One discrete fact, not bundled?
3. TAG_QUALITY -- type: and domain: present? Tags accurate?
4. ACTIONABILITY -- Useful if recalled in future conversation?

Return JSON: {"accuracy": N, "atomicity": N, "tag_quality": N, "actionability": N, "issues": ["..."]}
```

Scores 30 random memories per run. Cost: ~$0.005.

### CLI

```bash
python3 quality/quality_analyzer.py analyze
```

---

## Phase 5: Semantic Dedup Sweep (Quarterly)

Catches duplicates that 60% word-overlap misses (e.g., "User prefers dark mode" vs "Dark mode is preferred theme").

### Files

```
quality/dedup/
  __init__.py
  find_semantic_dupes.py   # Embed + cosine similarity to find candidates
  merge_duplicates.py      # GPT-4.1-mini decides: keep, merge, or delete
```

### How it works

1. Pull all active memories from SQLite
2. Compute pairwise cosine similarity on existing embeddings (from Azure AI Search)
3. Flag pairs with similarity > 0.85 (below the 0.60 word-overlap threshold)
4. Send each pair to GPT-4.1-mini: "Are these the same fact? If yes, produce merged version."
5. Output: list of merge/delete actions for human review

### CLI

```bash
# Dry run (show candidates, no changes)
python3 quality/quality_analyzer.py dedup --dry-run

# Apply merges
python3 quality/quality_analyzer.py dedup --apply
```

### Cost

~$0.05/run (depends on duplicate count). Run quarterly.

---

## Phase 6: A/B Comparison Framework (Quarterly)

Only run when you have a candidate extraction prompt to test.

### Files

```
quality/comparison/
  __init__.py
  select_test_sessions.py   # Stratified sample: 2 large, 3 medium, 2 small
  run_extraction.py          # Run extraction with a given prompt
  compare_results.py         # Diff: fact count, noise, tags, dedup rate
  format_comparison.py       # Render as markdown table
quality/data/
  candidate_prompt.txt       # Modified prompt for testing (optional)
```

### Flow

1. Select 7 representative sessions (stratified by size)
2. Run GPT-5.2 extraction with baseline prompt
3. Run GPT-5.2 extraction with candidate prompt from `data/candidate_prompt.txt`
4. Compare: fact count, noise ratio, tag quality %, dedup rate, confidence distribution
5. Output markdown table with winner per metric

### CLI

```bash
python3 quality/quality_analyzer.py compare
```

**Skipped if `data/candidate_prompt.txt` doesn't exist.** Cost: ~$1.40/run.

---

## Phase 7: Monthly Report + Cron

### Files

```
quality/reporting/
  __init__.py
  generate_report.py    # Assemble monthly markdown report
  trend_tracker.py      # Load/save historical metrics
quality/data/
  monthly_history.json  # Historical metrics for trends
```

### Report sections

| Section | Source | Cadence |
|---------|--------|---------|
| Executive Summary | 6 key metrics with month-over-month arrows | Monthly |
| Extraction Quality | Score distribution (accuracy, atomicity, tag quality, actionability) | Monthly |
| Pass Rate Trend | Last 6 months from extract_state.json | Monthly |
| Failure Modes | Noise / low-conf / dupe / secrets breakdown | Monthly |
| Tag Distribution | Top 15 tags, anchor coverage %, drift alerts | Monthly |
| Recall Benchmark | Precision@5, Recall@5, MRR + worst queries | Monthly |
| Semantic Dedup | Duplicate count, merge actions taken | Quarterly |
| A/B Comparison | Side-by-side metrics (if candidate prompt exists) | Quarterly |
| Recommendations | 3 actionable items from GPT-4.1-mini | Monthly |

### Cron

```bash
# Monthly quality report -- 1st of each month at 21:00 UTC
0 21 1 * * cd ~/.openclaw/workspace/skills/clawbot-memory && \
  .venv/bin/python3 quality/quality_analyzer.py report \
  >> ~/.openclaw/logs/quality-analysis/$(date -u +\%Y-\%m-\%d).log 2>&1

# Quarterly dedup sweep -- 1st of Jan/Apr/Jul/Oct at 21:30 UTC
30 21 1 1,4,7,10 * cd ~/.openclaw/workspace/skills/clawbot-memory && \
  .venv/bin/python3 quality/quality_analyzer.py dedup --apply \
  >> ~/.openclaw/logs/quality-analysis/$(date -u +\%Y-\%m-\%d)-dedup.log 2>&1
```

### CLI

```bash
python3 quality/quality_analyzer.py report
```

Reports saved to `quality/reports/YYYY-MM.md`.

---

## Phase 8: Core Infrastructure (Build Incrementally)

Built as each phase needs it — not upfront.

### Files

```
quality/
  __init__.py
  quality_analyzer.py   # CLI: analyze | tags | compare | benchmark | dedup | report
  config.py             # Constants, thresholds, paths, model names
  types.py              # Dataclasses: MemoryScore, TagAnalysis, RecallResult, CompareResult
```

### CLI subcommands

| Command | Phases | Cadence |
|---------|--------|---------|
| `tags` | 1 | Monthly |
| `benchmark` | 2 | Monthly |
| `analyze` | 4 | Monthly |
| `dedup` | 5 | Quarterly |
| `compare` | 6 | Quarterly / on-demand |
| `report` | 7 | Monthly (runs tags + benchmark + analyze + report) |

---

## File Structure (21 files + 3 data files)

```
quality/
  __init__.py
  quality_analyzer.py
  config.py
  types.py

  extraction/
    __init__.py
    sample_memories.py
    score_memory.py
    analyze_pass_rates.py
    identify_failure_modes.py

  tags/
    __init__.py
    analyze_distribution.py
    check_anchor_coverage.py
    find_promotion_candidates.py
    detect_tag_drift.py

  recall/
    __init__.py
    build_benchmark.py
    run_benchmark.py
    compute_metrics.py

  comparison/
    __init__.py
    select_test_sessions.py
    run_extraction.py
    compare_results.py
    format_comparison.py

  dedup/
    __init__.py
    find_semantic_dupes.py
    merge_duplicates.py

  reporting/
    __init__.py
    generate_report.py
    trend_tracker.py

  data/
    recall_benchmark.json
    monthly_history.json
    candidate_prompt.txt
```

23 Python files + 3 data files. Each file under 80 lines.

---

## Key Dependencies

| Dependency | Path | Purpose |
|------------|------|---------|
| smart_extractor.py | `oclaw_brain/update1/smart_extractor.py` | Extraction prompt, `extract_and_tag()` for A/B |
| memory_bridge.py | `oclaw_brain/update1/memory_bridge.py` | `AzureSearchBridge.search()`, scoring profile, categorize |
| mem.py | `oclaw_brain/oclaw_brain_skill_v1/cli/mem.py` | SQLite schema, query patterns |
| TAG_REGISTRY.md | `oclaw_brain/update1/TAG_REGISTRY.md` | Tag taxonomy |
| Existing venv | VM: `~/.openclaw/workspace/skills/clawbot-memory/.venv/` | openai, azure-search-documents |

---

## Cost Summary

| Cadence | Components | Cost/run | Annual |
|---------|-----------|----------|--------|
| Monthly | Scoring + tags + recall + report | ~$0.01 | ~$0.12 |
| Quarterly | A/B comparison + dedup sweep + TAG_REGISTRY review | ~$1.50 | ~$6.00 |
| **Total** | | | **~$6.12/year** |

---

## Verification Checklist

1. Phase 0 deployed, A/B shows improved tag diversity
2. Tag analysis shows anchor coverage baseline
3. Recall benchmark has 15-20 curated queries with baseline scores
4. Scoring profile tested on staging index, MRR improved
5. Extraction scoring returns valid 1-5 scores for all 4 dimensions
6. Dedup sweep finds and merges at least some semantic duplicates
7. Monthly cron produces report in `quality/reports/`
8. All success criteria metrics tracked in `monthly_history.json`
