# Decision: Does oclaw-search Basic Tier Include Azure Semantic Ranking?

**Date**: 2026-03-28
**Status**: Proposed — requires verification
**Deciders**: Des Villa
**Research source**: plans/research-log.md — "Memory Retrieval Best Practices 2025-2026"

## Context

Azure AI Search semantic ranking is a cross-encoder reranker that rescores the top-50 L1 results using Microsoft's language understanding models. Research confirms it measurably improves text query results over pure RRF ranking. However, semantic ranking availability depends on the Azure AI Search tier. The current `oclaw-search` resource is in the `oclaw-rg` resource group and costs ~$74/month, which corresponds to the Basic tier.

Per Microsoft documentation: Semantic ranking is available on Basic tier and above. However, the Basic tier has a lower free semantic ranking quota (1,000 queries/month free, then charged). Standard and above have higher quotas.

This decision matters because:
1. If semantic ranking IS available: the scoring profile behavior changes (text_weights are overridden; only scoring functions persist through semantic rerank)
2. If semantic ranking is NOT enabled: the scoring profile text_weights work normally; no change needed to Phase 3a of mem-optimize-v5.md

## Options Considered

### Option A: Assume Basic tier has semantic ranking, update scoring profile accordingly
- **Pros**: Proactive; avoids the bug where text_weights are silently discarded after semantic rerank
- **Cons**: If semantic ranking is not enabled, the change is unnecessary
- **Deployment impact**: Must use scoring functions (freshness/magnitude) instead of text_weights for durable boosting

### Option B: Verify first, then decide
- **Command**: `az search service show --name oclaw-search --resource-group oclaw-rg --query "sku"`
- **Then**: If sku is "basic" — check if `semanticSearch` property is enabled or "disabled"
- **Pros**: Correct, data-driven decision
- **Cons**: Requires one CLI call
- **Deployment impact**: None until verification completed

### Option C: Disable semantic ranking and rely on RRF + scoring profile only
- **Pros**: Avoids semantic ranking quota charges; scoring profile text_weights work as expected; simpler pipeline
- **Cons**: Loses the L2 reranking improvement; semantic ranking has demonstrated retrieval gains on text queries
- **Deployment impact**: Set `queryType: "semantic"` to off; remove semantic configuration

## Decision

**Execute Option B (verify first). Run the verification command and update this decision based on results.**

Verification commands:
```bash
# Check SKU
az search service show --name oclaw-search --resource-group oclaw-rg --query "sku.name" -o tsv

# Check semantic search configuration
az search service show --name oclaw-search --resource-group oclaw-rg --query "semanticSearch" -o tsv
```

Expected outputs:
- `sku.name`: "basic" → Basic tier confirmed
- `semanticSearch`: "free" or "standard" → semantic ranking is enabled; "disabled" → not available

**If semantic ranking is enabled (free tier):**
- Update mem-optimize-v5.md Phase 3a to note that text_weights do not survive semantic rerank
- Change scoring profile to rely only on magnitude functions (importance) and freshness functions
- Remove text_weights from the scoring profile spec

**If semantic ranking is disabled:**
- Keep text_weights in scoring profile as-is
- Semantic ranking pipeline notes in mem-optimize-v5.md do not apply
- RRF + scoring profile (including text_weights) is the full retrieval pipeline

## Consequences

**Easier:**
- Clear understanding of whether the L2 semantic reranker is in the pipeline
- Correct scoring profile design for whichever mode is active

**Harder:**
- If semantic ranking is enabled and we keep text_weights, they will be silently overridden after semantic rerank — a subtle bug that only appears in benchmark results

## Action Required

Run the verification command above before implementing Phase 3 of mem-optimize-v5.md or Round 3 of memory-recall-optimizer1.md.

## References

- [Azure AI Search — Semantic Ranking Overview](https://learn.microsoft.com/en-us/azure/search/semantic-search-overview)
- [Azure AI Search — Use Scoring Profiles with Semantic Ranking](https://learn.microsoft.com/en-us/azure/search/semantic-how-to-enable-scoring-profiles)
- [Microsoft Tech Community — Azure AI Search Hybrid + Semantic Ranking benchmarks](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/azure-ai-search-outperforming-vector-search-with-hybrid-retrieval-and-reranking/3929167)
- plans/research-log.md, entry dated 2026-03-28
- plans/mem-optimize-v5.md Phase 3a
