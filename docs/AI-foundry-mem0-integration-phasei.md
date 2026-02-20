# AI Foundry + Microsoft Agent Framework — mem0 Integration (Phase I / MVP)

Date: 2026-02-09

## Objective
Prove that **structured durable memory (mem0)** + **deterministic pruning** reduces **quality degradation** in long-running sessions (target **128k-token** context window), without relying on brittle “summarize inside reducer” behaviors.

## MVP principle
- **Prune first** (deterministic)
- Use **mem0** for continuity (structured durables only)
- Keep prompt injection **bounded** (top-k + token caps)

---

## Flow diagram (MVP: Prune reducer + mem0 only)

```
User msg
  |
  v
[Session history keeps growing]
  |
  v
[Token check vs 128k budget]
  |    (>= 50% used => prune)
  v
[Prune reducer]
  - keep last N turns (e.g., 20)
  - drop oldest turns
  |
  v
[mem0 retrieval (top-k durables)]
  - query = user msg (+ tags)
  - inject <= 4k–8k tokens
  |
  v
[LLM / Agent call]
  |
  v
[Durable extractor]
  - decisions / constraints / facts / artifact pointers
  |
  v
[mem0 upsert]
  (structured durables only)
```

## Why prune-first is the safest MVP for quality
- Matches MAF’s intended extension points (reducer + context provider-style injection).
- Avoids the “summarize too early and lose nuance” failure mode.
- mem0 proves value quickly: continuity without dragging full transcript.

## Suggested defaults (Phase I)
- **Prune** to last **N = 20 turns**
- **mem0 retrieval**: **10–15 items max**
- **Injected mem0 cap**: **4k–8k tokens**
- **Prune trigger**: **50% of 128k (~64k tokens)**

## What gets stored in mem0 (structured durables only)
Recommended minimal record types:
- **Decision**: statement + rationale + tags + source refs + confidence
- **Constraint**: constraint text + scope + tags + source refs
- **Artifact**: uri/pointer + description + provenance
- **Fact/Entity**: (subject, predicate, object) or small entity schema

## Phase II (next)
After Phase I is proven, add:
- Tier1 structured working state provider (goals/constraints/plan/open questions)
- Authority scoring + ratification for promoting items to shared memory
- Telemetry (token buckets, retrieval hit-rate, drift detection)
