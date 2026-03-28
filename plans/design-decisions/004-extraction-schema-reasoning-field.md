# Decision: Add `reasoning` Field to Fact Extraction JSON Schema

**Date**: 2026-03-28
**Status**: Proposed
**Deciders**: Research agent (flagged from research-log.md 2026-03-28 entry)

## Context

`smart_extractor.py` currently outputs facts as JSON with fields: `content`, `tags`, `importance`. The Claude-judge audit (2026-03-27) scored tag specificity at 2.41/5 and ClawBot utility at 1.79/5. The root cause is that the model assigns tags without being forced to commit to a rationale first — it defaults to safe, vague tags (`type:context`, `type:decision` for non-decisions) because there is no mechanism exposing the reasoning before the tags are locked.

## Options Considered

### Option A: Add `reasoning` field before `tags` in the JSON schema

The model fills a `reasoning` field (e.g., "This is an observed behavior, not a choice — type:fact is correct. The subject is the tailscale config — domain:infrastructure.") before outputting the `tags` field. JSON field ordering in the schema determines fill order for constrained generation models.

- **Pros**: Forces CoT-before-tags behavior at zero latency cost (same API call). Creates a per-fact audit trail for quality scoring. Directly addresses tag specificity problem. ~30–50 additional output tokens per fact.
- **Cons**: Slightly increases output token count (~+15%). Requires confirming that Azure OpenAI API respects field ordering in constrained generation (it does for GPT-5.x with `strict: true`).
- **Deployment impact**: Schema change in `smart_extractor.py` only; no SQLite schema changes needed (reasoning field is used for quality scoring only, not stored).

### Option B: Keep current schema, rely on definitions + examples only (Phase 0 plan)

Tag definitions and usage counts are added to the prompt (already planned). No structural schema change.

- **Pros**: Smaller change, faster to implement, easier to A/B test in isolation.
- **Cons**: Does not force the model to expose its tag rationale. Definitions reduce ambiguity but do not catch cases where the model correctly understands a definition but still assigns the wrong tag for a given fact.
- **Deployment impact**: 4 code edits to `smart_extractor.py`, no schema changes.

## Decision

**Proposed: Implement Option A as Layer 2, after measuring Option B as Layer 1 baseline.**

Do not skip the Layer 1 baseline (Phase 0 definitions + counts). The A/B test in `phase00-tag-definition-injection.md` will establish whether definitions alone reach the 4.0/5 target. If tag accuracy scores above 4.0 after Layer 1, Layer 2 is optional. If accuracy is still below 4.0 (likely, given that the audit found structural misclassification, not just ambiguity), implement Layer 2.

## Consequences

**Easier:**
- Monthly quality scoring cron can analyze `reasoning` field to identify systematic failure modes (e.g., "LLM reasons correctly but assigns wrong tag" vs "LLM misunderstands the fact category entirely")
- Future prompt improvements can target specific reasoning failure patterns rather than tag distributions in aggregate

**Harder:**
- `reasoning` field must be excluded from the memory `content` stored to SQLite (it is a schema field, not a memory field — store or discard after quality logging)
- If Azure OpenAI API version does not support field-ordered constrained generation, the benefit is lost (fallback: use `thinking` parameter if available, or accept the unordered case)

## References

- `plans/research-log.md` — 2026-03-28 entry: "LLM Fact Extraction Prompt Engineering"
- `plans/phase00-tag-definition-injection.md` — Layer 1 implementation plan
- `plans/tag-analysis-mar27/step4-claude-judge-report.md` — baseline quality audit
- arXiv:2511.22176 (Focused CoT), ICCV 2025W (Reasoning-Enhanced Multi-Label Classification)
