# Decision: Memory Keyword Extraction — Separate Field vs. Prefixed Tags Array

**Date**: 2026-03-28
**Status**: Proposed
**Deciders**: User + research agent (triggered by memory tagging best practices research)

## Context

The current oclaw_brain ClawBot memory system stores string tags in a single array per memory (e.g., `["type:decision", "domain:infrastructure", "pin:true"]`). Research into 2025-2026 production memory systems (Mem0, Zep, LangMem, A-MEM) shows that leading systems extract **keywords** as a distinct field separate from classification tags. Keywords are content terms (service names, error codes, proper nouns, concepts); classification tags are structural labels (`type:`, `domain:`).

Adding keyword extraction would enable BM25-style pre-filtering in Azure AI Search before semantic ranking — the standard production hybrid retrieval pattern. The decision is how to store these keywords without breaking the existing system.

## Options Considered

### Option A: Separate `keywords` field in Azure AI Search index

Store keywords as a dedicated `Collection(Edm.String)` field in the Azure Search index, separate from the existing `tags` array.

- **Pros**:
  - Clean separation of concerns — classification tags vs. content keywords
  - Azure Search can apply BM25 scoring specifically to the `keywords` field
  - Filtering syntax is unambiguous: `keywords/any(k: k eq 'tailscale')` vs tag filtering
  - Matches Mem0's architecture exactly (separate `categories` and `keywords` fields)
  - Future-proof for faceted search, analytics per keyword vs. tag type
- **Cons**:
  - Requires Azure Search index schema update (add new field)
  - Requires re-indexing all existing memories to populate the new field (existing entries will have `null` keywords)
  - `memory_bridge.py` and potentially `smart_extractor.py` need updates to push/read the new field
- **Deployment impact**: Medium — schema migration + re-index of existing memories. One-time cost. No data loss.

### Option B: `kw:` prefixed entries in the existing tags array

Store keywords as `kw:tailscale`, `kw:imds`, `kw:oauth` etc. in the same tags array as type/domain tags.

- **Pros**:
  - Zero schema changes — works with current Azure Search index immediately
  - Zero changes to `memory_bridge.py`
  - Can ship as a prompt-only change to `smart_extractor.py`
  - Backwards compatible with all existing filtering code
- **Cons**:
  - Mixed-type array makes filtering messier: must prefix-match `kw:` entries vs. exact-match `type:` entries
  - Azure BM25 scoring cannot distinguish keyword relevance from tag relevance
  - Array grows with keywords (3–5 keywords + 3–4 type/domain tags = 7–9 entries per memory vs. current 2–4)
  - Conflates two semantically different things into one field — harder to query "all memories about tailscale" cleanly
- **Deployment impact**: Minimal — extraction prompt change only.

## Decision

**Recommended: Option A (Separate `keywords` field)** for new memories going forward, with Option B as the immediate interim step.

Reasoning:
- The Mem0 production architecture explicitly separates `categories` and `keywords` — this is validated at scale
- Azure AI Search's hybrid scoring works best when keyword content and classification labels are in different fields
- The re-index cost is a one-time operation and the memory corpus is small (hundreds to low-thousands of entries)
- Option B is acceptable as a fast-follow interim (deploy prompt change immediately, schema migration in a separate task)

**Immediate action (zero-risk):** Update the tag extraction prompt in `smart_extractor.py` to extract keywords as `kw:`-prefixed entries in the tags array (Option B). This ships in minutes.

**Follow-up task (schema migration):** Add `keywords: Collection(Edm.String)` to the Azure Search index, update `memory_bridge.py` to split `kw:*` tags into the new field, and re-index. Schedule as a separate task.

## Consequences

- **Easier**: Hybrid retrieval queries in Azure AI Search (pre-filter by keyword before semantic ranking); analytics on what keywords appear most frequently; filtering memories by content term without knowing exact memory text
- **More difficult (short-term)**: Slightly more complex `memory_bridge.py` logic to split the tags array during indexing; one-time re-index required
- **No impact**: Existing type/domain/pin/permanent tag filtering is unchanged

## References

- Research log entry: `plans/research-log.md` — "Research: Memory Tagging and Classification Best Practices — Mem0, Zep, LangMem, Letta/MemGPT, A-MEM" (2026-03-28)
- [Mem0 Custom Categories](https://docs.mem0.ai/platform/features/custom-categories) — Project-level category definition with auto-assignment
- [Mem0 Enhanced Metadata Filtering](https://docs.mem0.ai/open-source/features/metadata-filtering) — `categories` and `keywords` as separate filter fields
- [A-MEM arXiv 2502.12110](https://arxiv.org/abs/2502.12110) — LLM-generated keywords + tags as separate note attributes
