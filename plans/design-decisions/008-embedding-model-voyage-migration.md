# Decision: Embedding Model — Stay on text-embedding-3-large or Migrate to Voyage-3.5

**Date**: 2026-03-28
**Status**: Proposed
**Deciders**: Des Villa
**Research source**: plans/research-log.md — "Memory Retrieval Best Practices 2025-2026"

## Context

Current model: `text-embedding-3-large` at 3072 dimensions via Azure OpenAI. Voyage AI released voyage-3-large (Jan 2025) and voyage-3.5 (current as of Mar 2026). On Voyage's RTEB benchmark (29 retrieval datasets, 8 domains), Voyage 4 Large outperforms text-embedding-3-large by 14% and Cohere embed-v4 by 8.2% on NDCG@10. Voyage-3-large shows +9.74% over text-embedding-3-large averaged over 100 datasets. Voyage supports Matryoshka representation learning (can truncate to 1024 dims without retraining) and int8 quantization.

For a 100-memory store, this decision primarily affects retrieval precision and storage costs. The Azure AI Search basic tier stores ~307K floats for 100 memories at 3072 dims vs ~102K floats at 1024 dims.

## Options Considered

### Option A: Stay on text-embedding-3-large (3072 dims)
- **Pros**: No migration; zero downtime; Azure OpenAI already authenticated; embedding cost included in existing Azure spend
- **Cons**: 3072 dims is oversized for a 100-memory store; not top-performing on retrieval benchmarks
- **Monthly cost**: Embedding model is pay-per-token; re-indexing 100 memories is ~$0.001 regardless of model
- **Deployment impact**: None

### Option B: Migrate to Voyage-3.5 (1024 dims)
- **Pros**: +9-14% on retrieval benchmarks; 67% smaller vector storage; slightly faster similarity search; Matryoshka allows further compression if needed
- **Cons**: New API key required (Voyage AI, not Azure); authentication change in memory_bridge.py; Azure index schema must be recreated (delete + recreate = brief downtime); adds external dependency outside Azure ecosystem
- **Cost**: Voyage-3-large pricing ~$0.06/M tokens; 100 memories × ~50 tokens = negligible
- **Deployment impact**: Azure index recreation (staging → production promotion via mem-optimize-v5.md Phase 3a protocol)

### Option C: Migrate to Cohere embed-v4 (1024 dims)
- **Pros**: Highest MTEB score (65.2 vs OpenAI 64.6); multimodal support (future-proofs for image memories); 128K context window
- **Cons**: Same migration overhead as Option B; Cohere API key required; multimodal feature irrelevant for text-only memories
- **Deployment impact**: Same as Option B

### Option D: Migrate to text-embedding-3-large at 1024 dims (Matryoshka truncation)
- **Pros**: No new API key; Azure OpenAI already configured; Matryoshka allows 1024-dim output from same model; reduces storage 67%
- **Cons**: Small performance loss (~2-3%) vs full 3072 dims; still underperforms Voyage on retrieval
- **Deployment impact**: Index schema update only (dimension change); re-sync required

## Decision

**Defer migration. Stay on text-embedding-3-large for current phase. Plan Option B (Voyage-3.5) as a combined migration with contextual re-indexing (Decision 007) on the next quarterly re-index.**

Rationale:
- For 100 memories, the retrieval improvement from embedding model alone is < 2-3 queries per 20-query benchmark — below the noise floor before RRF and contextual re-indexing are implemented
- The right time to migrate is when re-indexing anyway (contextual prefix addition per Decision 007)
- Adding an external API dependency (Voyage) should be evaluated after the Azure-native improvements are validated
- Option D (Matryoshka 1024 dims) is the zero-risk path if storage optimization is needed urgently

Trigger condition for migration:
- Round 4 benchmark shows retrieval plateau despite RRF + contextual re-indexing changes
- OR quarterly re-index is already happening for Decision 007 contextual prefix migration

## Consequences

**Easier:**
- Migration is a single well-scoped event (combined with contextual re-indexing)
- No authentication change until decision is triggered

**Harder:**
- May carry slightly lower retrieval quality than Voyage-3.5 in the interim
- 3072-dim vectors use 3x the storage of 1024-dim alternatives (trivial at 100 memories)

## References

- [Voyage AI — voyage-3-large launch](https://blog.voyageai.com/2025/01/07/voyage-3-large/)
- [Reintech — Embedding Models 2026 Comparison](https://reintech.io/blog/embedding-models-comparison-2026-openai-cohere-voyage-bge)
- [ailog.fr — Best Embedding Models 2025 MTEB](https://app.ailog.fr/en/blog/guides/choosing-embedding-models)
- plans/research-log.md, entry dated 2026-03-28
- plans/design-decisions/007-contextual-reindexing-memory-facts.md
