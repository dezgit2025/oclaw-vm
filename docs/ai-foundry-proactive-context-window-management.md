# AI Foundry V2 / Microsoft Agent Framework — Proactive Context Window Management

Date: 2026-02-09

Links reviewed:
- https://github.com/microsoft/agent-framework
- https://github.com/microsoft/Agent-Framework-Samples
- https://github.com/microsoft/Multi-Agent-Custom-Automation-Engine-Solution-Accelerator/tree/main

## What these repos imply about “context rot” risk

From the Agent Framework README, the framework is oriented around:
- **Agents** (chat/Responses style)
- **Workflows** (graph-based orchestration)
- **Middleware** (request/response processing hooks)
- **Checkpointing / time-travel** (workflow state)
- **Observability** (OpenTelemetry)

Those are exactly the right “insertion points” to solve context rot proactively:
- middleware can enforce token budgets + truncation rules
- workflows/checkpoints can persist *state* externally instead of keeping it all in prompt
- tracing can track prompt size and trigger compaction before failure

The “Multi-Agent Custom Automation Engine Solution Accelerator” describes a production-style architecture (multi-agent planning/execution/validation + Cosmos DB). That’s a natural home for **external memory** (like mem0) and **stateful, queryable conversation artifacts**.

## Definitions (so we’re aligned)

- **Context window management**: keeping the prompt under model limits *and* keeping the right information salient.
- **Context rot**: conversation grows; old details either crowd out important newer ones or cause the model to miss key constraints; worst case: hard failure due to prompt too large.
- **mem0** (as proposed here): a dedicated, external memory store that holds durable facts, decisions, artifacts, and summaries, with retrieval into prompt as needed.

---

## Five proactive best-practice suggestions (with simple diagrams)

### 1) Add a “token budget governor” middleware (hard gates + soft gates)
**Idea:** Every agent call goes through middleware that estimates tokens and enforces budgets. At **50% budget** you do a *soft* action (summarize/move-to-mem0). At **80–90%** you do a *hard* action (drop low-salience turns, force structured summary, block large tool outputs).

**Where it fits:** Agent Framework middleware layer (Python/.NET) and/or AI Foundry orchestration layer.

**Diagram**
```
User/Tool msg
   |
   v
[Middleware: token governor]
   |  if <50%: pass
   |  if 50-80%: compact + mem0 write
   |  if >80%: aggressive prune + artifact-only retrieval
   v
  LLM call
```

**Practical rules:**
- Budget prompt into buckets: `system+policy`, `task`, `recent turns`, `retrieved memory`, `tool results`.
- Cap tool results in-memory (e.g., store full output in blob/store, inject only a pointer + snippet).
- Track *per-turn* token deltas and raise alerts when a single tool output spikes.

**Why it helps:** prevents “sudden death” overflow; enforces predictability.

---

### 2) Use “state-first” orchestration: persist state in checkpoints/db, not in chat history
**Idea:** In multi-agent workflows, treat the chat as an *interaction log*, not the source of truth.

Persist the canonical state externally:
- requirements
- constraints
- plan
- decisions
- artifacts/URLs
- progress + open issues

Then each step retrieves only what it needs.

**Diagram**
```
            +-------------------+
            |  State Store      |
            | (Cosmos/mem0)     |
            +---------+---------+
                      ^
                      | read/write
                      |
Agent step A -----> Orchestrator -----> Agent step B
   (chat)              |                  (chat)
                       v
                 Minimal prompt
           (state + last N turns)
```

**In practice:**
- Use workflow **checkpoints** as first-class outputs: `PlanV3`, `RiskRegister`, `OpenQuestions`.
- On each node/agent step: hydrate prompt from `StateStore + last N turns`.

**Why it helps:** prevents long-running workflows from accumulating unbounded conversational baggage.

---

### 3) “Memory tiers” + mem0 promotion at 50% fullness (your idea, formalized)
**Idea:** Split memory into tiers and promote information upward when the window hits ~50%.

Memory tiers:
- **Tier 0 (hot):** last 10–30 turns (raw)
- **Tier 1 (warm):** running structured summary + current plan + constraints
- **Tier 2 (cold / mem0):** durable facts + decisions + artifact pointers + detailed transcripts

At ~50% estimated context fullness:
1) Extract “durables” (facts/decisions/artifacts) → write to mem0
2) Replace old turns with a structured summary (Tier 1)
3) Keep only the last N turns raw (Tier 0)

**Diagram**
```
Context window fullness
0% ---------50%----------100%
       | promote to mem0 |

Prompt = [System]
       + [Tier1 summary]
       + [Tier0 recent]
       + [mem0 retrieval (top-k)]
```

**Implementation detail:**
- Store mem0 records with schemas:
  - `Decision {id, date, rationale, impacts, tags}`
  - `Fact {subject, predicate, object, confidence, source}`
  - `Artifact {type, uri, checksum?, description}`
- Retrieval uses: tags + recency + task relevance.

**Why it helps:** keeps prompts small while retaining “long-term continuity.”

---

### 4) Use “artifact pointers” for large tool outputs (avoid stuffing raw outputs into chat)
**Idea:** Most context explosions happen when tool results (files, logs, HTML) are appended verbatim.

Instead:
- Store full output externally (blob/file/db)
- Inject into prompt:
  - a 1–2 paragraph summary
  - a small excerpt
  - a stable pointer: `artifact://…` or URL/file id

**Diagram**
```
Tool output (500KB)
   |
   v
[Artifact store]
  | store full
  v
Pointer + summary (<=2KB) ---> Prompt
```

**Best practice rules:**
- Enforce maximum “tool-to-context” ratio (e.g., no more than 20% of prompt from tool outputs).
- Always summarize + quote only the relevant parts.

**Why it helps:** prevents the exact failure mode described in your RCA (giant JSONL lines / tool dumps).

---

### 5) “Context health metrics” + proactive compaction triggers (observability-driven)
**Idea:** Treat context like a resource with SLOs.

Track and emit metrics via OpenTelemetry:
- estimated prompt tokens by bucket
- tool output sizes
- compaction frequency and effectiveness (bytes/tokens removed)
- mem0 writes + retrieval hit-rate
- “context risk score” (based on growth slope)

Trigger policies:
- **growth slope high** (e.g., +10% tokens/turn) → immediate compaction
- **tool output spike** → artifact pointer + forced summarization
- **50%** → mem0 promotion
- **80%** → aggressive pruning + require “state-first” prompt

**Diagram**
```
[Tracing/Metrics]
      |
      v
 Context Risk Score
      |
      +--> Compaction trigger
      +--> mem0 promotion
      +--> Alerts / dashboards
```

**Why it helps:** you stop guessing and start managing context proactively.

---

## How this maps to Agent Framework / AI Foundry V2 components

- **Agent Framework middleware**: best place to implement (1) token governor + (4) tool output pointering.
- **Workflows / checkpoints**: best place to implement (2) state-first orchestration.
- **Solution accelerator + Cosmos DB**: best place to implement (3) memory tiers + durable mem0 storage.
- **OpenTelemetry**: best place to implement (5) context health metrics.

## Questions to confirm before we implement

1) What is your target model family/context size in AI Foundry V2 (e.g., 128k vs 200k)?
2) Do you want mem0 to store **raw transcripts**, or only **structured durables** (facts/decisions/artifacts)?
3) How strict should we be at 50%?
   - A) always compact
   - B) compact only if growth slope suggests overflow in <N turns
4) For multi-agent: should each agent have its own memory namespace, or share a global mem0 with tags/ACLs?
5) What’s the failure mode we prioritize?
   - A) hard overflow prevention
   - B) quality degradation (“forgetting”) prevention
   - C) both equally

## Suggested next step (concrete)

If you answer the questions above, I’ll propose a minimal implementation plan:
- middleware token estimator + budget buckets
- mem0 schema + promotion policy
- artifact store interface
- tracing dashboards
- a small sample workflow from Agent-Framework-Samples updated to use it
