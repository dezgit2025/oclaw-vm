#!/usr/bin/env python3
"""
LLM-as-judge scorer for memory recall benchmark results.

Currently implements a deterministic rule-based scorer.
Can be upgraded to use an LLM judge when a model proxy is available.

Scores each query on two dimensions:
  - Relevance (1-5): How well the expected memory was ranked
  - Noise (1-5): How many unrelated results appear in top-K
"""

import argparse
import json
import sys
from datetime import datetime, timezone


def load_benchmark(baseline_path: str) -> dict:
    """Load the benchmark queries file referenced in the baseline."""
    with open(baseline_path) as f:
        baseline = json.load(f)
    # The benchmark file path is relative in the baseline; resolve it
    import os
    bench_path = baseline.get("benchmark_file", "")
    if not os.path.isabs(bench_path):
        bench_path = os.path.join(os.path.dirname(baseline_path), "..", "..", bench_path)
        bench_path = os.path.normpath(bench_path)
    with open(bench_path) as f:
        queries = json.load(f)
    return {q["id"]: q for q in queries}


def score_relevance(result: dict, benchmark_query: dict) -> dict:
    """Score relevance (1-5) based on rank position of expected memory ID."""
    expected_ids = set(result.get("expected_ids", []))
    recalled_ids = result.get("recalled_ids", [])
    expected_keywords = benchmark_query.get("expected_keywords", [])

    # Check rank of first expected ID
    best_rank = None
    for i, rid in enumerate(recalled_ids):
        if rid in expected_ids:
            best_rank = i + 1  # 1-indexed
            break

    if best_rank == 1:
        score = 5
        reasoning = f"Expected memory ID found at rank 1 (top result)."
    elif best_rank is not None and best_rank <= 3:
        score = 4
        reasoning = f"Expected memory ID found at rank {best_rank} (within top 3)."
    elif best_rank is not None and best_rank <= 5:
        score = 3
        reasoning = f"Expected memory ID found at rank {best_rank} (within top 5)."
    else:
        # Check if expected keywords appear in top 5 snippets
        snippets_text = " ".join(
            s.get("snippet", "") for s in result.get("recalled_snippets", [])[:5]
        ).lower()
        kw_found = [kw for kw in expected_keywords if kw.lower() in snippets_text]
        if len(kw_found) >= 2:
            score = 2
            reasoning = (
                f"Expected memory ID not in top 5, but {len(kw_found)} expected keywords "
                f"found in results: {kw_found}."
            )
        else:
            score = 1
            kw_str = f" Only {len(kw_found)} keyword(s) matched." if kw_found else " No keywords matched."
            reasoning = f"Expected memory ID not in top 5.{kw_str}"

    return {
        "query_id": result["query_id"],
        "dimension": "relevance",
        "score": score,
        "reasoning": reasoning,
        "model": "rule-based",
    }


def score_noise(result: dict, benchmark_query: dict) -> dict:
    """Score noise (1-5) based on how many top-5 results share keywords with the query."""
    query_text = result.get("query", "").lower()
    # Extract significant words from query (length > 3, skip common stop words)
    stop_words = {
        "what", "when", "where", "which", "that", "this", "does", "with",
        "about", "from", "have", "been", "were", "they", "their", "there",
        "will", "would", "could", "should", "into", "also", "more", "than",
        "then", "some", "only", "very", "just", "being", "over", "such",
        "after", "before", "between", "through", "during", "each", "made",
        "used", "considered",
    }
    query_words = set()
    for w in query_text.split():
        w_clean = w.strip("?.,!\"'()[]{}").lower()
        if len(w_clean) > 3 and w_clean not in stop_words:
            query_words.add(w_clean)

    snippets = result.get("recalled_snippets", [])[:5]
    unrelated_count = 0

    for snippet_obj in snippets:
        snippet_text = snippet_obj.get("snippet", "").lower()
        # A result is "related" if it shares at least one significant query word
        shared = [w for w in query_words if w in snippet_text]
        if not shared:
            unrelated_count += 1

    if unrelated_count == 0:
        score = 5
        reasoning = "All top 5 results share keywords with the query."
    elif unrelated_count == 1:
        score = 4
        reasoning = "1 unrelated result in top 5."
    elif unrelated_count == 2:
        score = 3
        reasoning = "2 unrelated results in top 5."
    elif unrelated_count == 3:
        score = 2
        reasoning = "3 unrelated results in top 5."
    else:
        score = 1
        reasoning = f"{unrelated_count} unrelated results in top 5."

    return {
        "query_id": result["query_id"],
        "dimension": "noise",
        "score": score,
        "reasoning": reasoning,
        "model": "rule-based",
    }


def main():
    parser = argparse.ArgumentParser(description="Judge recall benchmark results")
    parser.add_argument("--input", required=True, help="Path to baseline results JSON")
    parser.add_argument(
        "--dimensions",
        default="relevance,noise",
        help="Comma-separated dimensions to score (default: relevance,noise)",
    )
    parser.add_argument(
        "--model",
        default="rule-based",
        help="Model to use for judging (default: rule-based)",
    )
    parser.add_argument("--output", required=True, help="Path to write scores JSON")
    args = parser.parse_args()

    dimensions = [d.strip() for d in args.dimensions.split(",")]

    with open(args.input) as f:
        baseline = json.load(f)

    # Load benchmark queries for keyword info
    benchmark_queries = load_benchmark(args.input)

    results = baseline.get("results", [])
    scores = []

    for result in results:
        qid = result["query_id"]
        bench_q = benchmark_queries.get(qid, {})

        if "relevance" in dimensions:
            scores.append(score_relevance(result, bench_q))
        if "noise" in dimensions:
            scores.append(score_noise(result, bench_q))

    output = {
        "source_file": args.input,
        "model": args.model,
        "dimensions": dimensions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_scores": len(scores),
        "scores": scores,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    # Print summary
    for dim in dimensions:
        dim_scores = [s["score"] for s in scores if s["dimension"] == dim]
        if dim_scores:
            avg = sum(dim_scores) / len(dim_scores)
            print(f"{dim.capitalize():>10s}: avg={avg:.2f}  min={min(dim_scores)}  max={max(dim_scores)}  n={len(dim_scores)}")

    print(f"\nWrote {len(scores)} scores to {args.output}")


if __name__ == "__main__":
    main()
