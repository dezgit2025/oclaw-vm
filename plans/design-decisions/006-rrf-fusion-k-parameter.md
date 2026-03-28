# Decision: RRF k Parameter for 5-Query Memory Recall Fusion

**Date**: 2026-03-28
**Status**: Proposed
**Deciders**: Des Villa
**Research source**: plans/research-log.md — "Memory Retrieval Best Practices 2025-2026"

## Context

smart_extractor.py runs 5 parallel search queries per recall turn (topic + 4 expansions). Results are currently deduplicated and ranked by priority field. RRF (Reciprocal Rank Fusion) is a rank aggregation algorithm that scores results by their position across all result lists, rewarding documents that appear in multiple sub-query results. Research shows RRF yields +8-10% answer accuracy over single-query RAG and is strictly better than dedup+priority for combining parallel query results. Azure AI Search uses RRF natively for hybrid (BM25+vector) fusion with k=60.

## Options Considered

### Option A: Keep current dedup + priority sort
- **Pros**: No code change; already implemented
- **Cons**: Ignores cross-query rank signal; a memory appearing in 4/5 queries at rank 3 gets no boost over a memory appearing in 1/5 queries at rank 1
- **Deployment impact**: None

### Option B: RRF with k=60 (Azure default)
- **Pros**: Standard value; matches Azure's internal hybrid fusion; well-understood behavior
- **Cons**: k=60 was tuned for large document collections; for 5 queries × top-10 results, documents cluster at ranks 1-10, making k=60 dampen differentiation
- **Formula**: `score += 1 / (60 + rank)` → range ~0.016 to 0.017 for top-10 ranks (flat)
- **Deployment impact**: 15-line Python change to cmd_recall(); no new dependencies

### Option C: RRF with k=10 (small collection tuning)
- **Pros**: With 5 queries × top-10 results and 100 total memories, k=10 gives more spread: score range 0.045 to 0.091 for ranks 1-10 (2x differentiation vs k=60)
- **Cons**: Less tested; may over-weight rank-1 results from individual queries
- **Deployment impact**: Same as Option B

### Option D: RRF with k=60 + priority as tiebreaker
- **Pros**: Combines RRF signal with existing importance data; memories with same RRF score fall back to priority/importance
- **Cons**: Adds complexity; only matters when two memories have identical RRF scores (rare with 5 queries)
- **Deployment impact**: Slightly more code than Option B/C

## Decision

**Implement Option C (k=10) with priority as tiebreaker (Option D pattern).**

Rationale:
- For a 5-query × top-10-results fusion over 100 memories, k=10 provides meaningful rank differentiation where k=60 is nearly flat
- Priority as tiebreaker preserves existing importance signal at zero additional cost
- This is a backward-compatible change that can be A/B tested in Round 2 of the recall benchmark

Implementation target: `smart_extractor.py` → `cmd_recall()`, replace current dedup logic.

```python
def rrf_fuse(result_lists: list[list[dict]], k: int = 10) -> list[dict]:
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for result_list in result_lists:
        for rank, item in enumerate(result_list, start=1):
            mem_id = item["id"]
            scores[mem_id] = scores.get(mem_id, 0) + 1.0 / (k + rank)
            items[mem_id] = item
    return sorted(
        items.values(),
        key=lambda x: (-scores[x["id"]], -x.get("priority", 0))
    )
```

## Consequences

**Easier:**
- Memories that appear in multiple expansion query results naturally float to the top
- No new API calls or dependencies

**Harder:**
- Slightly harder to explain why a specific memory was top-ranked (rank fusion is less intuitive than "priority=9")
- Need to verify k=10 experimentally in Round 2 benchmark; may need to adjust to k=20 or k=60

## References

- [RAG-Fusion paper](https://arxiv.org/abs/2402.03367)
- [Azure AI Search RRF docs](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)
- plans/research-log.md, entry dated 2026-03-28
- plans/memory-recall-optimizer1.md Round 2
