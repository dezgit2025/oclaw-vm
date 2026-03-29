#!/usr/bin/env python3
"""Run recall benchmark queries against a local SQLite memory DB.

Supports two modes:
  - baseline: Single keyword search (original logic from mem.py cmd_search)
  - rrf: Reciprocal Rank Fusion — expand each query into sub-queries,
         run each independently, fuse results with RRF scoring

Usage:
    python run_benchmark.py \
        --benchmark quality/data/recall_benchmark.json \
        --db memory.db \
        --output quality/data/round2-results.json \
        --mode rrf
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path


# ── Stopwords for query expansion ──────────────────────────────────
STOPWORDS = frozenset(
    "a an the is are was were be been being do does did has have had "
    "will would shall should can could may might must need ought dare "
    "in on at to for of from by with about between through during "
    "and or but nor not so yet both either neither "
    "it its he she they them their his her this that these those "
    "what which who whom how when where why "
    "i me my we us our you your "
    "if then else than "
    "all each every some any no none few many much more most "
    "very too also just only even still already "
    "s t re ve ll d m".split()
)


def search_memories(conn, query: str, k: int = 5):
    """Search memories using the same logic as mem.py cmd_search."""
    query_words = query.lower().split()
    rows = conn.execute(
        "SELECT id, content, tags, importance FROM memories WHERE active=1 ORDER BY created_at DESC"
    ).fetchall()

    scored = []
    for row in rows:
        mid, content, tags, importance = row
        content_lower = content.lower()
        score = sum(1 for w in query_words if w in content_lower)
        if score > 0:
            scored.append({
                "id": mid,
                "content": content,
                "tags": tags,
                "importance": importance,
                "score": score,
            })

    scored.sort(key=lambda x: -x["score"])
    return scored[:k]


# ── RRF: Query Expansion ──────────────────────────────────────────

def expand_query(query: str):
    """Expand a benchmark query into 3-5 sub-queries for broader recall.

    Strategy:
      1. Original query (full)
      2. Key terms only (stopwords removed)
      3. Individual significant words (2+ chars, not stopwords)
      4. Bigrams of significant words
    """
    sub_queries = [query]  # Always include the original

    # Extract significant words
    words = re.findall(r"[a-zA-Z0-9][\w\-]*", query.lower())
    sig_words = [w for w in words if w not in STOPWORDS and len(w) > 2]

    # Sub-query 2: key terms joined
    if len(sig_words) >= 2:
        sub_queries.append(" ".join(sig_words))

    # Sub-query 3+: individual significant words (top 3 longest — likely most specific)
    unique_sig = list(dict.fromkeys(sig_words))  # dedupe preserving order
    by_length = sorted(unique_sig, key=len, reverse=True)
    for w in by_length[:3]:
        if w not in sub_queries:
            sub_queries.append(w)

    # Sub-query: bigrams of significant words (adjacent pairs)
    if len(unique_sig) >= 2:
        for i in range(min(len(unique_sig) - 1, 3)):
            bigram = f"{unique_sig[i]} {unique_sig[i+1]}"
            if bigram not in sub_queries:
                sub_queries.append(bigram)

    # Cap at 8 sub-queries to stay fast
    return sub_queries[:8]


# ── RRF: Fusion ───────────────────────────────────────────────────

def rrf_fuse(ranked_lists, k_param: int = 10):
    """Reciprocal Rank Fusion across multiple ranked result lists.

    For each memory, compute:
        RRF_score = SUM[ 1 / (k_param + rank) ]  over all lists containing it

    Args:
        ranked_lists: list of lists, each list is ranked search results
                      (list of dicts with at least 'id', 'content', 'tags', 'importance')
        k_param: smoothing constant (default 10, lower = more weight on top ranks)

    Returns:
        Fused list sorted by RRF score descending, with 'score' set to RRF score.
    """
    rrf_scores = {}  # id -> cumulative RRF score
    mem_data = {}    # id -> memory dict (content, tags, importance)

    for result_list in ranked_lists:
        for rank_idx, mem in enumerate(result_list):
            mid = mem["id"]
            rrf_scores[mid] = rrf_scores.get(mid, 0.0) + 1.0 / (k_param + rank_idx + 1)
            if mid not in mem_data:
                mem_data[mid] = {
                    "id": mid,
                    "content": mem["content"],
                    "tags": mem["tags"],
                    "importance": mem["importance"],
                }

    # Build fused list
    fused = []
    for mid, rrf_score in rrf_scores.items():
        entry = dict(mem_data[mid])
        entry["score"] = round(rrf_score, 6)
        fused.append(entry)

    fused.sort(key=lambda x: -x["score"])
    return fused


def search_memories_rrf(conn, query: str, k: int = 5):
    """RRF-enhanced search: expand query, run sub-queries, fuse results."""
    sub_queries = expand_query(query)

    # Run each sub-query independently, fetch more candidates per sub-query
    per_query_k = max(k * 3, 15)  # fetch more to give RRF good material
    ranked_lists = []
    for sq in sub_queries:
        results = search_memories(conn, sq, k=per_query_k)
        if results:
            ranked_lists.append(results)

    if not ranked_lists:
        return []

    fused = rrf_fuse(ranked_lists, k_param=10)
    return fused[:k]


# ── Benchmark Runner ──────────────────────────────────────────────

def run_benchmark(benchmark_path: str, db_path: str, k: int = 5, mode: str = "baseline"):
    """Run all benchmark queries and return results."""
    with open(benchmark_path) as f:
        queries = json.load(f)

    conn = sqlite3.connect(db_path)

    search_fn = search_memories_rrf if mode == "rrf" else search_memories

    results = []
    for q in queries:
        recalled = search_fn(conn, q["query"], k=k)
        recalled_ids = [r["id"] for r in recalled]
        expected_ids = q.get("expected_memory_ids", [])

        # Determine hits: expected IDs found in recalled IDs
        hits = [eid for eid in expected_ids if eid in recalled_ids]
        misses = [eid for eid in expected_ids if eid not in recalled_ids]

        result = {
            "query_id": q["id"],
            "query": q["query"],
            "category": q.get("category", ""),
            "difficulty": q.get("difficulty", ""),
            "expected_ids": expected_ids,
            "recalled_ids": recalled_ids,
            "recalled_snippets": [
                {"id": r["id"], "score": r["score"], "snippet": r["content"][:200]}
                for r in recalled
            ],
            "hits": hits,
            "misses": misses,
            "hit": len(misses) == 0 and len(expected_ids) > 0,
        }
        results.append(result)

    conn.close()
    return results


def print_summary(results, mode="baseline"):
    """Print hit/miss summary stats."""
    total = len(results)
    hit_count = sum(1 for r in results if r["hit"])
    miss_count = total - hit_count

    print(f"\n{'='*60}")
    print(f"RECALL BENCHMARK RESULTS  (mode={mode})")
    print(f"{'='*60}")
    print(f"Total queries:  {total}")
    print(f"Hits:           {hit_count}  ({100*hit_count/total:.1f}%)")
    print(f"Misses:         {miss_count}  ({100*miss_count/total:.1f}%)")
    print(f"{'='*60}")

    # Breakdown by category
    categories = {}
    for r in results:
        cat = r["category"] or "unknown"
        if cat not in categories:
            categories[cat] = {"total": 0, "hits": 0}
        categories[cat]["total"] += 1
        if r["hit"]:
            categories[cat]["hits"] += 1

    print(f"\nBy category:")
    for cat, stats in sorted(categories.items()):
        pct = 100 * stats["hits"] / stats["total"]
        print(f"  {cat:12s}: {stats['hits']}/{stats['total']}  ({pct:.0f}%)")

    # Breakdown by difficulty
    difficulties = {}
    for r in results:
        diff = r["difficulty"] or "unknown"
        if diff not in difficulties:
            difficulties[diff] = {"total": 0, "hits": 0}
        difficulties[diff]["total"] += 1
        if r["hit"]:
            difficulties[diff]["hits"] += 1

    print(f"\nBy difficulty:")
    for diff, stats in sorted(difficulties.items()):
        pct = 100 * stats["hits"] / stats["total"]
        print(f"  {diff:12s}: {stats['hits']}/{stats['total']}  ({pct:.0f}%)")

    # Show misses
    missed = [r for r in results if not r["hit"]]
    if missed:
        print(f"\nMissed queries:")
        for r in missed:
            print(f"  [{r['query_id']}] {r['query'][:80]}")
            print(f"    expected: {r['expected_ids']}")
            print(f"    recalled: {r['recalled_ids'][:3]}{'...' if len(r['recalled_ids']) > 3 else ''}")


def main():
    parser = argparse.ArgumentParser(description="Run recall benchmark against memory DB")
    parser.add_argument("--benchmark", required=True, help="Path to benchmark JSON file")
    parser.add_argument("--db", required=True, help="Path to SQLite memory DB")
    parser.add_argument("--output", required=True, help="Path to write results JSON")
    parser.add_argument("-k", type=int, default=5, help="Top-k results per query (default: 5)")
    parser.add_argument("--mode", choices=["baseline", "rrf"], default="rrf",
                        help="Search mode: baseline (single query) or rrf (multi-query fusion, default)")
    args = parser.parse_args()

    # Validate inputs
    if not Path(args.benchmark).exists():
        print(f"Error: benchmark file not found: {args.benchmark}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.db).exists():
        print(f"Error: database not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    # Run benchmark
    results = run_benchmark(args.benchmark, args.db, k=args.k, mode=args.mode)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "benchmark_file": args.benchmark,
        "db_file": args.db,
        "k": args.k,
        "mode": args.mode,
        "total_queries": len(results),
        "total_hits": sum(1 for r in results if r["hit"]),
        "total_misses": sum(1 for r in results if not r["hit"]),
        "hit_rate": sum(1 for r in results if r["hit"]) / len(results) if results else 0,
        "results": results,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: {args.output}")
    print_summary(results, mode=args.mode)


if __name__ == "__main__":
    main()
