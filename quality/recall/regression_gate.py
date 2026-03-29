#!/usr/bin/env python3
"""
Regression gate for memory recall benchmark.

Computes metrics from judge scores and baseline results:
  - Precision@5: fraction of queries where expected memory ID appears in top 5
  - MRR: mean reciprocal rank of first expected memory ID
  - Weighted judge score: (Relevance_avg * 0.3 + Noise_avg * 0.1) / 0.4, normalized to 5-point scale

Supports two modes:
  --baseline FILE        Single-file mode: compute and print metrics
  --before F --after F   Comparison mode: compute deltas and check regression thresholds
"""

import argparse
import json
import sys


def load_scores(path: str) -> dict:
    """Load a scores JSON file produced by judge_recall.py."""
    with open(path) as f:
        return json.load(f)


def load_baseline_results(scores_data: dict) -> dict:
    """Load the original baseline results referenced by the scores file."""
    source = scores_data.get("source_file", "")
    with open(source) as f:
        return json.load(f)


def compute_precision_at_k(results: list, k: int = 5) -> float:
    """Fraction of queries where at least one expected ID appears in top-K recalled IDs."""
    if not results:
        return 0.0
    hits = 0
    for r in results:
        expected = set(r.get("expected_ids", []))
        recalled = r.get("recalled_ids", [])[:k]
        if expected & set(recalled):
            hits += 1
    return hits / len(results)


def compute_mrr(results: list, k: int = 5) -> float:
    """Mean Reciprocal Rank: average of 1/rank for first expected ID in top-K, 0 if not found."""
    if not results:
        return 0.0
    reciprocal_ranks = []
    for r in results:
        expected = set(r.get("expected_ids", []))
        recalled = r.get("recalled_ids", [])[:k]
        rr = 0.0
        for i, rid in enumerate(recalled):
            if rid in expected:
                rr = 1.0 / (i + 1)
                break
        reciprocal_ranks.append(rr)
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def compute_judge_averages(scores_data: dict) -> dict:
    """Compute per-dimension averages from judge scores."""
    scores = scores_data.get("scores", [])
    by_dim = {}
    for s in scores:
        dim = s["dimension"]
        by_dim.setdefault(dim, []).append(s["score"])
    return {dim: sum(vals) / len(vals) for dim, vals in by_dim.items()}


def compute_weighted_score(relevance_avg: float, noise_avg: float) -> float:
    """Weighted judge score: (Relevance_avg * 0.3 + Noise_avg * 0.1) / 0.4"""
    return (relevance_avg * 0.3 + noise_avg * 0.1) / 0.4


def compute_all_metrics(scores_data: dict) -> dict:
    """Compute all metrics from a scores file."""
    baseline = load_baseline_results(scores_data)
    results = baseline.get("results", [])

    p5 = compute_precision_at_k(results, k=5)
    mrr = compute_mrr(results, k=5)
    avgs = compute_judge_averages(scores_data)
    rel_avg = avgs.get("relevance", 0.0)
    noise_avg = avgs.get("noise", 0.0)
    weighted = compute_weighted_score(rel_avg, noise_avg)

    return {
        "precision_at_5": p5,
        "mrr": mrr,
        "relevance_avg": rel_avg,
        "noise_avg": noise_avg,
        "weighted_score": weighted,
        "total_queries": len(results),
        "total_hits": sum(1 for r in results if r.get("hit", False)),
        "total_misses": sum(1 for r in results if not r.get("hit", False)),
    }


def print_metrics(metrics: dict, label: str = "Baseline"):
    """Pretty-print metrics."""
    print(f"\n{'=' * 50}")
    print(f"  {label} Metrics")
    print(f"{'=' * 50}")
    print(f"  Precision@5:      {metrics['precision_at_5']:.3f}  ({metrics['total_hits']}/{metrics['total_queries']} queries hit)")
    print(f"  MRR:              {metrics['mrr']:.3f}")
    print(f"  Relevance avg:    {metrics['relevance_avg']:.2f} / 5.00")
    print(f"  Noise avg:        {metrics['noise_avg']:.2f} / 5.00")
    print(f"  Weighted score:   {metrics['weighted_score']:.2f} / 5.00")
    print(f"{'=' * 50}\n")


def print_comparison(before: dict, after: dict):
    """Print side-by-side comparison with deltas."""
    print(f"\n{'=' * 65}")
    print(f"  Regression Gate: Before vs After")
    print(f"{'=' * 65}")
    print(f"  {'Metric':<20s} {'Before':>8s} {'After':>8s} {'Delta':>8s} {'Status':>10s}")
    print(f"  {'-' * 58}")

    # Thresholds: regression if metric drops by more than this
    thresholds = {
        "precision_at_5": 0.05,
        "mrr": 0.05,
        "relevance_avg": 0.25,
        "noise_avg": 0.25,
        "weighted_score": 0.20,
    }

    any_regression = False
    for key, label in [
        ("precision_at_5", "Precision@5"),
        ("mrr", "MRR"),
        ("relevance_avg", "Relevance avg"),
        ("noise_avg", "Noise avg"),
        ("weighted_score", "Weighted score"),
    ]:
        b = before[key]
        a = after[key]
        delta = a - b
        threshold = thresholds[key]

        if delta < -threshold:
            status = "REGRESSED"
            any_regression = True
        elif delta > threshold:
            status = "IMPROVED"
        else:
            status = "OK"

        print(f"  {label:<20s} {b:>8.3f} {a:>8.3f} {delta:>+8.3f} {status:>10s}")

    print(f"  {'-' * 58}")
    if any_regression:
        print(f"  RESULT: REGRESSION DETECTED")
    else:
        print(f"  RESULT: PASS (no regression)")
    print(f"{'=' * 65}\n")

    return not any_regression


def main():
    parser = argparse.ArgumentParser(description="Compute recall benchmark metrics and check regressions")
    parser.add_argument("--baseline", help="Single scores file to compute metrics for")
    parser.add_argument("--before", help="Scores file for the 'before' run (comparison mode)")
    parser.add_argument("--after", help="Scores file for the 'after' run (comparison mode)")
    args = parser.parse_args()

    if args.baseline:
        scores = load_scores(args.baseline)
        metrics = compute_all_metrics(scores)
        print_metrics(metrics, label="Baseline")
        return

    if args.before and args.after:
        before_scores = load_scores(args.before)
        after_scores = load_scores(args.after)
        before_metrics = compute_all_metrics(before_scores)
        after_metrics = compute_all_metrics(after_scores)

        print_metrics(before_metrics, label="Before")
        print_metrics(after_metrics, label="After")
        passed = print_comparison(before_metrics, after_metrics)

        if not passed:
            sys.exit(1)
        return

    parser.error("Provide either --baseline FILE or --before FILE --after FILE")


if __name__ == "__main__":
    main()
