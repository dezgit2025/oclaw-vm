# Memory Extraction Quality Optimization Plan (v4)

## Context

ClawBot's memory system extracts facts from conversation sessions via GPT-5.2, stores them in SQLite, and syncs to Azure AI Search (`clawbot-memory-store` index, 3072-dim `text-embedding-3-large` embeddings). The system has been running since 2026-02-23 with a 71% extraction pass rate but **no quality feedback loop exists**. Tags are LLM-assigned (hybrid: LLM generates + rules enforce anchors), but there's no measurement of tag accuracy, recall quality, or extraction drift over time.

**This plan adds a Monthly Memory Quality Analyzer** — a lightweight analysis pipeline that scores extraction quality, benchmarks recall, optimizes tags, and supports A/B prompt comparison.

---

## Answers to Key Questions

### Are tags auto-assigned by LLM?
**Yes — hybrid approach.** The LLM (GPT-5.2) generates tags as part of the JSON extraction response, guided by the TAG_REGISTRY reference in the prompt. Then rules enforce:
- `decided:YYYY-MM-DD` auto-added to `type:decision` and `type:pivot` if missing
- `status:active` auto-added to decisions/pivots if missing
- `confidence:low` auto-added if confidence < 0.7
- New/unknown tags auto-logged to TAG_REGISTRY.md for promotion review
- Max 8 tags per memory (schema-enforced)

### Should we do test extractions for comparison?
**Yes.** A/B extraction comparison on 5-10 representative sessions lets us measure prompt changes before deploying. Cost: ~$1.40/run with GPT-5.2.

### How to optimize tag assignment?
Three approaches combined:
1. **Measure anchor coverage** — what % of memories have `type:` and `domain:` tags
2. **Detect tag drift** — LLM inventing inconsistent near-duplicate tags
3. **Score tag quality** — GPT-4.1-mini rates tag accuracy on sampled memories

---

## Phase 0: Tag Definition Injection (Immediate Win)

### Problem
`extract_known_tags()` parses TAG_REGISTRY.md but only extracts **tag names**, not definitions. The LLM sees:
```
TAG REGISTRY (use these, or create new if needed):
  type: decision, pivot, preference, hypothesis, validation, error_pattern, ...
  domain: product, growth, monetization, funding, legal, ...
```
It does NOT see "pivot = reversal of a previous decision" or "validation = hypothesis confirmed or killed". This causes:
- Misclassification (e.g., `type:decision` used for observations that aren't choices)
- Under-use of specific tags (e.g., `type:validation`, `type:competitive`)
- Over-use of safe defaults (`type:context`, `type:insight`)

### Solution
Modify `extract_known_tags()` to also extract one-line definitions from the TAG_REGISTRY.md tables, and build `tag_ref` with definitions + usage counts.

### Files to Modify

**`/Users/dez/Projects/oclaw_brain/update1/smart_extractor.py`** — 3 changes:

#### Change 1: `extract_known_tags()` returns definitions (lines 260-272)

Current:
```python
def extract_known_tags(registry: str) -> dict:
    tags = {}
    dim = None
    for line in registry.split("\n"):
        dm = re.match(r"###\s+`(\w+):`", line)
        if dm:
            dim = dm.group(1)
            tags[dim] = []
        tm = re.match(r"\|\s*`(\w[\w:_-]+\w)`\s*\|", line)
        if tm and dim:
            tags[dim].append(tm.group(1))
    return tags
```

New — returns `dict[str, list[tuple[str, str]]]` (name, definition):
```python
def extract_known_tags(registry: str) -> dict:
    tags = {}
    dim = None
    for line in registry.split("\n"):
        dm = re.match(r"###\s+`(\w+):`", line)
        if dm:
            dim = dm.group(1)
            tags[dim] = []
        # Match: | `tag_name` | definition text | ...
        tm = re.match(r"\|\s*`([\w:_-]+)`\s*\|\s*([^|]+)", line)
        if tm and dim:
            tag_name = tm.group(1).split(":")[-1]  # strip prefix
            definition = tm.group(2).strip().rstrip("|").strip()
            tags[dim].append((tag_name, definition))
    return tags
```

#### Change 2: `tag_ref` includes definitions + counts (lines 307-308)

Current:
```python
known = extract_known_tags(load_tag_registry())
tag_ref = "\n".join(f"  {d}: {', '.join(v)}" for d, v in known.items())
```

New — query SQLite for usage counts, build rich reference:
```python
known = extract_known_tags(load_tag_registry())
tag_counts = _get_tag_usage_counts()  # new helper
tag_ref_lines = []
for dim, entries in known.items():
    tag_ref_lines.append(f"  {dim}:")
    for name, definition in entries:
        full_tag = f"{dim}:{name}"
        count = tag_counts.get(full_tag, 0)
        count_hint = f" ({count} uses)" if count > 0 else ""
        tag_ref_lines.append(f"    {name}{count_hint} -- {definition}")
tag_ref = "\n".join(tag_ref_lines)
```

#### Change 3: New helper `_get_tag_usage_counts()` (add near line 258)

```python
def _get_tag_usage_counts() -> dict:
    """Count tag usage from SQLite for frequency hints."""
    counts = {}
    try:
        import sqlite3
        db_path = os.path.expanduser("~/.claude-memory/memory.db")
        if not os.path.exists(db_path):
            return counts
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT tags FROM memories WHERE active=1").fetchall()
        conn.close()
        for (tags_str,) in rows:
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag:
                    counts[tag] = counts.get(tag, 0) + 1
    except Exception:
        pass  # non-critical — return empty counts
    return counts
```

#### Change 4: Tighten prompt wording (line 321)

Current:
```
TAG REGISTRY (use these, or create new if needed):
```

New:
```
TAG REGISTRY (PREFER these — only create new if NONE fit):
```

### What the LLM will now see

Before:
```
TAG REGISTRY (use these, or create new if needed):
  type: decision, pivot, preference, hypothesis, validation, ...
  domain: product, growth, monetization, funding, ...
```

After:
```
TAG REGISTRY (PREFER these — only create new if NONE fit):
  type:
    decision (47 uses) -- A choice made between alternatives
    pivot (8 uses) -- A reversal of a previous decision
    preference (12 uses) -- A stated or inferred preference
    hypothesis -- An untested assumption
    validation -- A hypothesis confirmed or killed
    error_pattern (3 uses) -- A recurring error and its cause
    ...
  domain:
    infrastructure (31 uses) -- Cloud, devops, CI/CD, deployment
    ai (22 uses) -- AI features, embeddings, agents, memory
    product (5 uses) -- Core product features, UX, design
    ...
```

### Token cost impact
~200 extra tokens per extraction call. At GPT-5.2 rates (~$2/1M input), this adds ~$0.0004 per call. Negligible.

### Update to `update_tag_registry()` and `store_facts()`

`update_tag_registry()` (line 275) uses `extract_known_tags()` to build `all_known`. Since the return type changes from `list[str]` to `list[tuple[str, str]]`, update line 279-280:

Current:
```python
for vals in extract_known_tags(registry).values():
    all_known.update(vals)
```

New:
```python
for entries in extract_known_tags(registry).values():
    all_known.update(name for name, _ in entries)
```

Same fix needed in `store_facts()` (line 454):
```python
for v in extract_known_tags(load_tag_registry()).values():
    all_known.update(v)
```
becomes:
```python
for entries in extract_known_tags(load_tag_registry()).values():
    all_known.update(name for name, _ in entries)
```

### Testing

#### Test 1: Unit test `extract_known_tags()` with definitions
```python
# test_extract_known_tags.py
def test_extracts_names_and_definitions():
    registry = """### `type:` -- What kind?
| Tag | Definition | Example |
|-----|-----------|---------|
| `type:decision` | A choice made between alternatives | "Chose X" |
| `type:pivot` | A reversal of a previous decision | "Switched from X" |
"""
    result = extract_known_tags(registry)
    assert "type" in result
    assert result["type"][0] == ("decision", "A choice made between alternatives")
    assert result["type"][1] == ("pivot", "A reversal of a previous decision")

def test_handles_empty_registry():
    assert extract_known_tags("") == {}

def test_handles_missing_definitions():
    registry = """### `type:`
| Tag | Definition |
| `type:foo` | |
"""
    result = extract_known_tags(registry)
    assert result["type"][0][0] == "foo"
    assert result["type"][0][1] == ""  # empty definition ok
```

#### Test 2: Unit test `_get_tag_usage_counts()` with mock DB
```python
# test_get_tag_usage_counts.py
import sqlite3, tempfile, os

def test_counts_tags(tmp_path, monkeypatch):
    db = tmp_path / "memory.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE memories (tags TEXT, active INTEGER)")
    conn.execute("INSERT INTO memories VALUES ('type:decision, domain:ai', 1)")
    conn.execute("INSERT INTO memories VALUES ('type:decision, domain:infra', 1)")
    conn.execute("INSERT INTO memories VALUES ('type:context', 1)")
    conn.execute("INSERT INTO memories VALUES ('type:old', 0)")  # inactive
    conn.commit()
    conn.close()
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(db) if "memory.db" in p else p)
    # ... patch to use tmp db path
    counts = _get_tag_usage_counts()
    assert counts["type:decision"] == 2
    assert counts["domain:ai"] == 1
    assert "type:old" not in counts  # inactive excluded

def test_returns_empty_on_missing_db(tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path / "nope.db"))
    assert _get_tag_usage_counts() == {}
```

#### Test 3: Integration test — `tag_ref` format validation
```python
# test_tag_ref_format.py
def test_tag_ref_includes_definitions():
    """Verify the prompt injection has definitions, not just names."""
    known = extract_known_tags(load_tag_registry())
    counts = _get_tag_usage_counts()
    # Build tag_ref same as in extract_and_tag()
    tag_ref_lines = []
    for dim, entries in known.items():
        tag_ref_lines.append(f"  {dim}:")
        for name, definition in entries:
            full_tag = f"{dim}:{name}"
            count = counts.get(full_tag, 0)
            count_hint = f" ({count} uses)" if count > 0 else ""
            tag_ref_lines.append(f"    {name}{count_hint} -- {definition}")
    tag_ref = "\n".join(tag_ref_lines)

    assert "-- A choice made between alternatives" in tag_ref
    assert "  type:" in tag_ref
    assert "  domain:" in tag_ref
    # Should NOT be flat comma-separated anymore
    assert "type: decision, pivot" not in tag_ref

def test_tag_ref_shows_counts():
    """If memories exist, counts should appear."""
    # ... setup with mock DB containing tagged memories
    tag_ref = build_tag_ref()  # helper
    assert " uses)" in tag_ref
```

#### Test 4: `update_tag_registry()` still works with new return type
```python
# test_update_tag_registry.py
def test_update_detects_new_tags(tmp_path):
    registry_path = tmp_path / "TAG_REGISTRY.md"
    registry_path.write_text("""### `type:`
| Tag | Definition |
| `type:decision` | A choice |

## Free Tags
| Tag | First seen | Count | Promote? |
|-----|-----------|-------|----------|
""")
    # ... patch TAG_REGISTRY_PATH
    update_tag_registry(["type:decision", "type:brand_new_tag"])
    content = registry_path.read_text()
    assert "brand_new_tag" in content
    assert content.count("decision") == 1  # not duplicated
```

#### Test 5: A/B extraction comparison (manual, on VM)
```bash
# Run extraction on a known session with OLD prompt (flat tag list)
python3 smart_extractor.py extract --session SESSION_ID --dry-run > /tmp/baseline.json

# Deploy the new code
# Run extraction on SAME session with NEW prompt (definitions + counts)
python3 smart_extractor.py extract --session SESSION_ID --dry-run > /tmp/candidate.json

# Compare:
# - Are type: and domain: tags more accurate?
# - Did tag diversity improve (less type:context overuse)?
# - Did fact count stay similar (not extracting more noise)?
# - Did any new free-form tags get invented unnecessarily?
diff <(jq '.[].tags' /tmp/baseline.json) <(jq '.[].tags' /tmp/candidate.json)
```

#### Test 6: Backward compatibility — `store_facts()` all_known set
```python
# test_store_facts_compat.py
def test_all_known_set_works():
    """Verify store_facts builds all_known correctly with tuple return."""
    known = extract_known_tags(load_tag_registry())
    all_known = set()
    for entries in known.values():
        all_known.update(name for name, _ in entries)
    assert "decision" in all_known
    assert "product" in all_known
    assert isinstance(all_known.pop(), str)  # not tuple
```

---

## File Structure

All source at `/Users/dez/Projects/oclaw_brain/quality/`, deployed to VM at `~/.openclaw/workspace/skills/clawbot-memory/quality/`.

```
quality/
  __init__.py
  quality_analyzer.py          # CLI: analyze | tags | compare | benchmark | report
  config.py                    # Constants, thresholds, paths, model names
  types.py                     # Dataclasses: MemoryScore, TagAnalysis, RecallResult, CompareResult

  extraction/
    __init__.py
    sample_memories.py          # Pull N random memories from SQLite
    score_memory.py             # GPT-4.1-mini scores on 4 dimensions
    analyze_pass_rates.py       # Parse extract_state.json for trends
    identify_failure_modes.py   # Classify rejections by type

  comparison/
    __init__.py
    select_test_sessions.py     # Stratified session sampling (2 large, 3 med, 2 small)
    run_extraction.py           # Run extraction with a given prompt
    compare_results.py          # Diff two runs: fact count, noise, tags, dedup
    format_comparison.py        # Render as markdown table

  tags/
    __init__.py
    analyze_distribution.py     # Tag frequency from SQLite (pure Python, no LLM)
    check_anchor_coverage.py    # % with type: and domain: present
    find_promotion_candidates.py # Free-form tags with 5+ uses
    detect_tag_drift.py         # Word overlap to find near-duplicate tags

  recall/
    __init__.py
    build_benchmark.py          # Create/load benchmark queries + expected memory IDs
    run_benchmark.py            # Execute queries against Azure AI Search
    compute_metrics.py          # Precision@k, Recall@k, MRR

  reporting/
    __init__.py
    generate_report.py          # Assemble monthly markdown report
    trend_tracker.py            # Load/save historical metrics

  data/
    recall_benchmark.json       # Curated test queries (start with 15-20)
    monthly_history.json        # Historical metrics for trends
    candidate_prompt.txt        # Optional: modified prompt for A/B testing
```

21 Python files + 3 data files. Each file under 80 lines.

---

## Component Details

### 1. Extraction Quality Scoring

**What:** Sample 30 random memories, send each to GPT-4.1-mini for scoring.

**Scoring prompt (per memory):**
```
Score this extracted memory on 4 dimensions (1-5):

MEMORY: "{content}"
TAGS: [{tags}]
PROJECT: {project}

1. ACCURACY — Real verifiable fact, not hallucination or opinion?
2. ATOMICITY — One discrete fact, not bundled?
3. TAG_QUALITY — type: and domain: present? Tags accurate?
4. ACTIONABILITY — Useful if recalled in future conversation?

Return JSON: {"accuracy": N, "atomicity": N, "tag_quality": N, "actionability": N, "issues": ["..."]}
```

**Cost:** ~$0.005/run (9K tokens at GPT-4.1-mini rates)

### 2. A/B Extraction Comparison

**Flow:**
1. `select_test_sessions.py` — stratified sample: 2 large (>500KB), 3 medium, 2 small sessions
2. `run_extraction.py` — call GPT-5.2 with baseline prompt, then candidate prompt
3. `compare_results.py` — diff on: fact count, noise ratio, tag quality %, dedup rate, confidence distribution, unique signals
4. `format_comparison.py` — markdown table with winner per metric

**Candidate prompt:** Place modified prompt in `data/candidate_prompt.txt`. If file doesn't exist, comparison section is skipped in report.

**Cost:** ~$1.40/run (240K tokens at GPT-5.2 rates)

### 3. Tag Analysis (Zero LLM Cost)

| Analysis | Method |
|----------|--------|
| Distribution | COUNT + GROUP BY on tags column from SQLite |
| Anchor coverage | % of memories with `type:` tag, `domain:` tag, both |
| Promotion candidates | Parse TAG_REGISTRY.md, compare to actual usage, flag 5+ use free-form tags |
| Drift detection | Group by dimension prefix, word overlap >50% between tags in same dimension |

### 4. Recall Quality Benchmark

**Setup (one-time):** Curate 15-20 test queries in `recall_benchmark.json`:
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

**Run:** Execute each query against Azure AI Search via `AzureSearchBridge.search()`, record returned IDs + positions.

**Metrics:** Precision@5, Recall@5, MRR. Zero LLM cost (Azure Search queries free on basic tier).

**Bootstrap:** `build_benchmark.py init` can auto-generate candidate queries by asking GPT-4.1-mini "What question would this memory answer?" for top memories, then human reviews.

### 5. Monthly Report

Saved to `quality/reports/YYYY-MM.md`. Template includes:

| Section | Content |
|---------|---------|
| Executive Summary | 6 key metrics with month-over-month arrows |
| Extraction Quality | Score distribution table (accuracy, atomicity, tag quality, actionability) |
| Pass Rate Trend | Last 6 months |
| Failure Modes | Noise / low-conf / dupe / secrets breakdown |
| Tag Distribution | Top 15 tags, anchor coverage %, promotion candidates, drift alerts |
| Recall Benchmark | Precision@5, Recall@5, MRR + worst queries |
| A/B Comparison | Side-by-side metrics table (if candidate prompt exists) |
| Recommendations | 3 actionable items from GPT-4.1-mini analysis |

---

## Monthly Cost Budget

| Component | Cost/run |
|-----------|---------|
| Quality scoring (GPT-4.1-mini, 30 memories) | $0.005 |
| Failure mode analysis (GPT-4.1-mini) | $0.003 |
| Tag analysis (pure Python) | $0.00 |
| Recall benchmark (Azure Search) | $0.00 |
| A/B comparison (GPT-5.2, 8 sessions x2) | $1.40 |
| Report recommendations (GPT-4.1-mini) | $0.002 |
| **Total** | **~$1.41/month** |

---

## Cron Schedule (VM)

```bash
# Monthly quality report — 1st of each month at 21:00 UTC
0 21 1 * * cd ~/.openclaw/workspace/skills/clawbot-memory && \
  .venv/bin/python3 quality/quality_analyzer.py report \
  >> ~/.openclaw/logs/quality-analysis/$(date -u +\%Y-\%m-\%d).log 2>&1
```

---

## Implementation Phases

### Phase 1: Core infrastructure (~2h)
- `quality/` dir structure, `__init__.py`, `config.py`, `types.py`
- `quality_analyzer.py` CLI skeleton with subcommand routing
- `reporting/trend_tracker.py` for history persistence

### Phase 2: Extraction quality (~2h)
- `extraction/sample_memories.py`
- `extraction/score_memory.py`
- `extraction/analyze_pass_rates.py`
- `extraction/identify_failure_modes.py`

### Phase 3: Tag analysis (~1.5h)
- `tags/analyze_distribution.py`
- `tags/check_anchor_coverage.py`
- `tags/find_promotion_candidates.py`
- `tags/detect_tag_drift.py`

### Phase 4: Recall benchmark (~2h)
- `recall/build_benchmark.py` + initial `recall_benchmark.json`
- `recall/run_benchmark.py`
- `recall/compute_metrics.py`

### Phase 5: A/B comparison (~2h)
- `comparison/select_test_sessions.py`
- `comparison/run_extraction.py`
- `comparison/compare_results.py`
- `comparison/format_comparison.py`

### Phase 6: Report + deploy (~1.5h)
- `reporting/generate_report.py`
- Wire `report` subcommand
- Deploy to VM via scp
- Add monthly cron
- Run first baseline report

### Phase 7: Recall Tuning (~2.5h)

Three infrastructure changes to improve recall accuracy. No LLM cost — all pure config/code changes. Measure impact using the recall benchmark from Phase 4.

#### 7a. Azure Scoring Profile (~1h)

Add a scoring profile to the `clawbot-memory-store` index that boosts `importance` and freshness.

**File:** `/Users/dez/Projects/oclaw_brain/update1/memory_bridge.py` — index definition (~line 550)

Add to the index creation:
```python
ScoringProfile(
    name="memory-relevance",
    text_weights=TextWeights(weights={"content": 1.5, "tags": 1.0}),
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
            freshness=FreshnessFunction(boosting_duration="P30D"),  # 30-day decay
        ),
    ],
)
```

Then set `scoring_profile="memory-relevance"` in the search call (~line 195).

**Effect:** High-importance recent memories rank above old low-importance context. A memory rated importance=8 updated yesterday beats importance=3 from 2 weeks ago.

**Testing:**
```bash
# Before: run recall benchmark, save baseline
python3 quality/quality_analyzer.py benchmark > /tmp/recall-before.json

# Deploy scoring profile (requires index update — may need delete+recreate)
# After: run recall benchmark again
python3 quality/quality_analyzer.py benchmark > /tmp/recall-after.json

# Compare precision@5 and MRR
diff /tmp/recall-before.json /tmp/recall-after.json
```

**Risk:** Index schema change may require index recreation. If so, `memory_bridge.py sync --full` re-uploads all memories. Test on a staging index first if concerned.

#### 7b. Tag-Boosted Search (~45min)

Inject tag terms into the search query so BM25 matches on the `tags` field.

**File:** `/Users/dez/Projects/oclaw_brain/update1/memory_bridge.py` — search method (~line 182)

Current:
```python
results = client.search(
    search_text=query,
    ...
)
```

New — append tag hints to search text:
```python
def _enrich_query_with_tags(query: str) -> str:
    """Add tag terms to query for BM25 boosting on tags field."""
    tag_hints = []
    # Decision-intent signals
    if any(w in query.lower() for w in ["decided", "chose", "decision", "picked", "selected"]):
        tag_hints.append("type:decision")
    if any(w in query.lower() for w in ["error", "bug", "broke", "failed", "fix"]):
        tag_hints.append("type:error_pattern")
    if any(w in query.lower() for w in ["cost", "price", "spend", "budget", "$"]):
        tag_hints.append("domain:monetization")
    if any(w in query.lower() for w in ["deploy", "infra", "server", "vm", "azure", "docker"]):
        tag_hints.append("domain:infrastructure")
    if any(w in query.lower() for w in ["model", "llm", "gpt", "claude", "embedding", "ai"]):
        tag_hints.append("domain:ai")
    if not tag_hints:
        return query
    return f"{query} {' '.join(tag_hints)}"

results = client.search(
    search_text=_enrich_query_with_tags(query),
    ...
)
```

**Effect:** Query "what model does the gateway use" becomes "what model does the gateway use domain:ai" — BM25 now matches memories tagged `domain:ai`, boosting relevant results.

**Testing:**
```python
# test_enrich_query.py
def test_decision_query():
    assert "type:decision" in _enrich_query_with_tags("pricing decision")

def test_infra_query():
    assert "domain:infrastructure" in _enrich_query_with_tags("azure vm deploy")

def test_no_hints_for_generic():
    q = "weekly team update"
    assert _enrich_query_with_tags(q) == q  # no tags appended

def test_multiple_hints():
    enriched = _enrich_query_with_tags("azure cost decision")
    assert "domain:infrastructure" in enriched
    assert "domain:monetization" in enriched
    assert "type:decision" in enriched
```

Plus recall benchmark before/after comparison (same as 7a).

#### 7c. Category from Tags (~45min)

Replace keyword heuristics in `categorize_memory()` with tag-derived category.

**File:** `/Users/dez/Projects/oclaw_brain/update1/memory_bridge.py` — `categorize_memory()` (~line 287)

Current (keyword heuristics):
```python
def categorize_memory(content):
    if any(w in content.lower() for w in ["chose", "decided"]): return "decision"
    if any(w in content.lower() for w in ["prefers", "likes"]): return "preference"
    ...
    return "general"
```

New (tag-derived):
```python
def categorize_memory(content: str, tags: str = "") -> str:
    """Derive category from LLM-assigned tags, falling back to content heuristics."""
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
    # Fallback to content heuristics for memories without tags
    if any(w in content.lower() for w in ["chose", "decided"]):
        return "decision"
    if any(w in content.lower() for w in ["prefers", "likes"]):
        return "preference"
    return "general"
```

Update the call site in `daily_sync()` (~line 330) to pass tags:
```python
"category": categorize_memory(mem["content"], mem.get("tags", "")),
```

**Effect:** Category field becomes consistent with LLM tags. Enables accurate category-based filtering in future recall queries.

**Testing:**
```python
# test_categorize_memory.py
def test_tags_override_content():
    # Content says "decided" but tags say error_pattern
    assert categorize_memory("decided to debug", "type:error_pattern") == "error_pattern"

def test_tags_take_priority():
    assert categorize_memory("some text", "type:decision, domain:ai") == "decision"
    assert categorize_memory("some text", "type:preference") == "preference"

def test_fallback_to_content():
    assert categorize_memory("User decided to use React", "") == "decision"

def test_fallback_to_general():
    assert categorize_memory("random note", "") == "general"

def test_pivot_maps_to_decision():
    assert categorize_memory("switched approach", "type:pivot") == "decision"
```

After deploying, run `memory_bridge.py sync --full` to re-categorize all existing memories.

---

## Key Dependencies

| Dependency | Path | Purpose |
|------------|------|---------|
| smart_extractor.py | `oclaw_brain/update1/smart_extractor.py` | Extraction prompt baseline, `extract_and_tag()` for A/B |
| memory_bridge.py | `oclaw_brain/update1/memory_bridge.py` | `AzureSearchBridge.search()` for recall benchmark |
| mem.py | `oclaw_brain/oclaw_brain_skill_v1/cli/mem.py` | SQLite schema, query patterns |
| TAG_REGISTRY.md | `oclaw_brain/update1/TAG_REGISTRY.md` | Tag taxonomy for promotion analysis |
| Existing venv | VM: `~/.openclaw/workspace/skills/clawbot-memory/.venv/` | Already has openai, azure-search-documents |

---

## Verification

1. **Unit test each module** — run with `--dry-run` flag that uses cached data instead of LLM calls
2. **First baseline report** — run `quality_analyzer.py report` manually, verify all sections populate
3. **Recall benchmark** — confirm Azure Search returns results for test queries
4. **A/B comparison** — run with identical baseline/candidate prompt, verify diff shows 0 difference
5. **Tag analysis** — cross-check distribution against manual `SELECT tags FROM memories` query
6. **Cron verification** — check `~/.openclaw/logs/quality-analysis/` for report on the 2nd of next month
