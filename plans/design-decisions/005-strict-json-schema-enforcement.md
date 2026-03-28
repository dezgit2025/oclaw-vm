# Decision: Switch to `strict: true` JSON Schema Enforcement for Fact Extraction

**Date**: 2026-03-28
**Status**: Proposed
**Deciders**: Research agent (flagged from research-log.md 2026-03-28 entry)

## Context

The Claude-judge audit (2026-03-27) identified two structural tag bugs that JSON Schema enforcement would eliminate entirely:
1. **Invented free-form tags** (40 out of 70 unique tags are outside the TAG_REGISTRY — `tags:geo-search`, `tag:folder_organization`, meta-prefix anti-patterns)
2. **Dual conflicting tags** (6 memories have both `confidence:medium` AND `confidence:low` on the same memory — the extractor is not deduplicating within a tag slot)

These bugs are not addressable through prompt wording alone — they require structural enforcement. OpenAI's `response_format` with `strict: true` guarantees schema adherence for GPT-5.x models.

## Options Considered

### Option A: Use `response_format` with `strict: true` and JSON Schema

Define the output schema explicitly: `content` (string), `reasoning` (string), `tags` (string — comma-separated, validated downstream), `importance` (integer, 1–5). Set `strict: true` in the API call.

- **Pros**: Eliminates free-form tag format bugs. Eliminates importance format inconsistencies (e.g., `"importance": "high"` instead of `"importance": 4`). Eliminates `confidence:medium,confidence:low` dual-tag bug (enforced by string validation in caller). No invented keys.
- **Cons**: Requires Azure OpenAI API version `2024-08-01-preview` or later. Need to confirm current VM endpoint supports this. One-time migration of caller parsing code.
- **Deployment impact**: Edit `smart_extractor.py` to pass `response_format`; update caller to use schema-validated parsing instead of `json.loads()`.

### Option B: Keep current free-text JSON parsing, add post-extraction validation

Add a Python validation step after `json.loads()` that strips invalid tags, deduplicates tag slots, and coerces importance to int.

- **Pros**: No API version dependency. Works with any model.
- **Cons**: Fixes symptoms not the cause. Validation logic must be maintained separately. Still costs tokens on the invented/invalid tags before they get stripped.
- **Deployment impact**: Add a `validate_extraction()` function to `smart_extractor.py`.

## Decision

**Proposed: Implement Option A for Azure OpenAI API version >= 2024-08-01-preview, with Option B as fallback if the version check fails.**

The structural enforcement is the right fix. Add a version check at startup; if strict mode is unavailable, fall back to Option B validation. This makes the code robust across Azure OpenAI API version updates.

## Consequences

**Easier:**
- Tag format bugs eliminated at the source
- `store_facts()` caller can trust the schema without defensive parsing
- Monthly tag distribution analysis will reflect actual LLM choices, not formatting accidents

**Harder:**
- All output fields must be in `required`; need defaults or explicit handling for optional fields
- If Azure API version changes, strict mode behavior may change — add integration test that asserts no invented keys in extraction output

## References

- `plans/research-log.md` — 2026-03-28 entry: "LLM Fact Extraction Prompt Engineering"
- `plans/tag-analysis-mar27/step3-tag-distribution-report.md` — free-form tag problem documented
- `plans/tag-analysis-mar27/step4-claude-judge-report.md` — dual confidence tag bug documented
- [OpenAI Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs)
