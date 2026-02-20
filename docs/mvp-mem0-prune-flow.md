# MVP Flow: Prune Reducer + Tier1 State + mem0 (PoC)

Goal: prevent **quality degradation** in long-running agent sessions (128k context target) by:
- **Pruning** chat history (keep only last N turns)
- Maintaining a small, structured **Tier1 Working State**
- Using **mem0** as the durable store (structured facts/decisions/artifacts)

This MVP intentionally avoids “summarize inside reducer” to keep behavior deterministic and safe.

---

## High-level flow (single agent run)

```
                  (persisted across runs)
        +------------------------------------+
        | mem0 (durables store)              |
        | - constraints / decisions / facts  |
        | - artifact pointers                |
        +------------------+-----------------+
                           ^
                           |  (A) upsert new durables (post-run)
                           |
User message               |
     |                     |
     v                     |
+-------------------------------+
| 1) Session history (raw)      |
|    messages keep growing      |
+---------------+---------------+
                |
                | 2) Token budget check (128k target)
                |    - at 50% used => prune
                v
+-------------------------------+
| 3) Prune reducer              |
|    keep last N turns          |
|    drop oldest turns          |
+---------------+---------------+
                |
                | 4) Build prompt from 3 sources
                v
+-------------------------------+
| 5) Prompt assembler           |
|   - System instructions       |
|   - Tier1 working state       |
|   - last N turns (raw)        |
|   - mem0 retrieval (top-k)    |  <--- (B) retrieve relevant durables
+---------------+---------------+
                |
                v
+-------------------------------+
| 6) LLM / Agent call           |
+---------------+---------------+
                |
                | 7) Post-run extract durables
                v
+-------------------------------+
| 8) Durable extractor          |
|   - decisions/constraints     |
|   - artifact pointers         |
|   - updates to Tier1          |
+-------+-----------------------+
        |
        +----> update Tier1 store (structured)
        |
        +----> (A) upsert to mem0
```

Key: **mem0 is not the transcript**. It stores only *structured durables*.

---

## MVP “mem0-only PoC” variant (no fancy Tier1 yet)

If you want the absolute smallest proof of concept first:
- reducer prunes to last N turns
- post-run extracts durables to mem0
- next run retrieves top-k durables from mem0

Tier1 can be added after mem0 is proven to help.

```
User msg
  |
  v
[Prune to last N turns]
  |
  v
[mem0 retrieve top-k durables] ---> inject into prompt
  |
  v
LLM call
  |
  v
[Extract durables] ---> upsert to mem0
```

Recommended defaults for PoC:
- N = 20 turns (adjust)
- mem0 retrieve limit = 10–15 items
- retrieved mem0 token cap = 4k–8k tokens
- compaction trigger = 50% of 128k (~64k tokens)

---

## Why prune-first is safest (quality)

- Deterministic: no LLM summarization step that might drop critical details.
- mem0 retrieval is explicit and bounded (top-k + token cap).
- You can gradually improve extraction quality without risking prompt blowups.

---

## Next step to make this real

To implement this in Microsoft Agent Framework Python:
- ChatHistoryProvider + reducer (keep last N)
- AIContextProvider #1: mem0 retrieval (Invoking)
- AIContextProvider #2: mem0 extraction/upsert (Invoked)

Then later:
- Add Tier1 working state provider (structured summary) to further stabilize quality.
